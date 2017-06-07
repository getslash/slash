import sys
import os
import subprocess
import time
import logbook
import threading
from  six.moves import xmlrpc_client
from datetime import datetime
from .. import log
from ..exceptions import ParallelServerIsDown
from ..exceptions import INTERRUPTION_EXCEPTIONS
from ..conf import config
from ..ctx import context
from .server import Server
from ..utils.tmux_utils import create_new_window, kill_tmux_session

_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')

COMMUNICATION_TIMEOUT_SECS = 5
MAX_CONNECTION_RETRIES = 10

class ParallelManager(object):
    def __init__(self, args):
        super(ParallelManager, self).__init__()
        self.server = None
        self.args = [sys.executable, '-m', 'slash.frontend.main', 'run', '--parallel_parent_session_id', context.session.id] + args
        self.workers_num = config.root.parallel.num_workers
        self.workers = {}
        self.max_worker_id = 0
        self.server_thread = None

    def try_connect(self):
        num_retries = 0
        while not self.server.is_initialized:
            time.sleep(1)
            if num_retries == MAX_CONNECTION_RETRIES:
                raise ParallelServerIsDown("Cannot connect to XML_RPC server")
            num_retries += 1

    def start_worker(self):
        worker_id = str(self.max_worker_id)
        _logger.notice("Starting worker number {}".format(worker_id))
        new_args = self.args[:] + ["--parallel_worker_id", worker_id]
        if config.root.run.tmux:
            new_args.append(';$SHELL')
            command = ' '.join(new_args)
            self.workers[worker_id] = create_new_window("worker {}".format(worker_id), command)
        else:
            with open(os.devnull, 'w') as devnull:
                proc = subprocess.Popen(new_args, stdin=devnull, stdout=devnull, stderr=devnull)
                self.workers[worker_id] = proc
        self.max_worker_id += 1


    def start_server_in_thread(self, collected):
        self.server = Server(collected)
        self.server_thread = threading.Thread(target=self.server.serve, args=())
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def stop_server(self):
        client = xmlrpc_client.ServerProxy('http://{0}:{1}'.format(config.root.parallel.server_addr, self.server.port))
        client.stop_server()

    def start_workers(self):
        self.try_connect()
        if not config.root.parallel.server_port:
            self.args.extend(['--parallel_port', str(self.server.port)])
        for _ in range(self.workers_num):
            self.start_worker()
        try:
            while self.server.has_more_tests():
                workers_last_connection_time = self.server.get_workers_last_connection_time()
                for worker_id in workers_last_connection_time:
                    delta = (datetime.now() - workers_last_connection_time[worker_id]).seconds
                    if delta > COMMUNICATION_TIMEOUT_SECS:
                        if not config.root.run.tmux:
                            _logger.error("Worker {} is down, restarting".format(worker_id))
                            if self.workers[worker_id].poll() is None:
                                _logger.error("Killing worker {}".format(worker_id))
                                self.workers[worker_id].kill()
                        else:
                            self.workers[worker_id].rename_window('stopped_client_{}'.format(worker_id))
                        self.server.report_client_failure(worker_id)
                        self.start_worker()
                time.sleep(COMMUNICATION_TIMEOUT_SECS)
        except INTERRUPTION_EXCEPTIONS:
            _logger.error("Server interrupted, stopping workers and terminating")
            if config.root.run.tmux:
                kill_tmux_session()
            else:
                for worker in self.workers.values():
                    worker.kill()
                self.stop_server()
                raise
        finally:
            if not config.root.run.tmux:
                for worker in self.workers.values():
                    worker.wait()
                self.server_thread.join()
