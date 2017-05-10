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

_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')

COMMUNICATION_TIMEOUT_SECS = 5
MAX_CONNECTION_RETRIES = 10

class ParallelManager(object):
    def __init__(self, args):
        super(ParallelManager, self).__init__()
        self.server = None
        self.args = [sys.executable, '-m', 'slash.frontend.main', 'run'] + args
        self.workers_num = config.root.run.parallel
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
        with open(os.devnull, 'w') as devnull:
            proc = subprocess.Popen(self.args[:] + \
                    ["--worker_id", worker_id, "--master_session_id", context.session.id], stdin=devnull, stdout=devnull, stderr=devnull)
            self.workers[worker_id] = proc
            self.max_worker_id += 1

    def start_server_in_thread(self, collected):
        self.server = Server(collected)
        self.server_thread = threading.Thread(target=self.server.serve, args=())
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def stop_server(self):
        client = xmlrpc_client.ServerProxy('http://{0}:{1}'.format(config.root.run.server_addr, config.root.run.server_port))
        client.stop_server()

    def start_workers(self):
        self.try_connect()
        for _ in range(self.workers_num):
            self.start_worker()
        try:
            while self.server.has_more_tests():
                workers_last_connection_time = self.server.get_workers_last_connection_time()
                for worker_id in workers_last_connection_time:
                    delta = (datetime.now() - workers_last_connection_time[worker_id]).seconds
                    if delta > COMMUNICATION_TIMEOUT_SECS:
                        _logger.error("Worker {} is down, restarting".format(worker_id))
                        if self.workers[worker_id].poll() is None:
                            _logger.error("Killing worker {}".format(worker_id))
                            self.workers[worker_id].kill()
                        self.server.report_client_failure(worker_id)
                        self.start_worker()
                time.sleep(COMMUNICATION_TIMEOUT_SECS)
        except INTERRUPTION_EXCEPTIONS:
            for worker in self.workers.values():
                worker.kill()
            self.stop_server()
            raise
        finally:
            for worker in self.workers.values():
                worker.wait()
            self.server_thread.join()
