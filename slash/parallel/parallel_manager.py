import sys
import errno
import os
import signal
import subprocess
import time
import logbook
import threading
from tempfile import mkdtemp
from  six.moves import xmlrpc_client
from .. import log
from ..exceptions import INTERRUPTION_EXCEPTIONS, ParallelServerIsDown, ParallelTimeout
from ..conf import config
from ..ctx import context
from .server import Server, ServerStates
from ..utils.tmux_utils import create_new_window, create_new_pane
from .worker_configuration import WorkerConfiguration
from .._compat import iteritems
from .. import hooks

_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')

TIME_BETWEEN_CHECKS = 2
MAX_CONNECTION_RETRIES = 200

class ParallelManager(object):
    def __init__(self, args):
        super(ParallelManager, self).__init__()
        self.server = None
        self.workers_error_dircetory = mkdtemp()
        self.args = [sys.executable, '-m', 'slash.frontend.main', 'run', '--parallel-parent-session-id', context.session.id, \
                    '--workers-error-dir', self.workers_error_dircetory] + args
        self.workers_num = config.root.parallel.num_workers
        self.workers = {}
        self.max_worker_id = 1
        self.server_thread = None

    def try_connect(self):
        num_retries = 0
        while self.server.state == ServerStates.NOT_INITIALIZED:
            time.sleep(0.1)
            if num_retries == MAX_CONNECTION_RETRIES:
                raise ParallelServerIsDown("Cannot connect to XML_RPC server")
            num_retries += 1

    def start_worker(self):
        worker_id = str(self.max_worker_id)
        _logger.notice("Starting worker number {}".format(worker_id))
        new_args = self.args[:] + ["--parallel-worker-id", worker_id]
        worker_config = WorkerConfiguration(new_args)
        hooks.before_worker_start(worker_config=worker_config) # pylint: disable=no-member
        if config.root.tmux.enabled:
            worker_config.argv.append(';$SHELL')
            command = ' '.join(worker_config.argv)
            if config.root.tmux.use_panes:
                self.workers[worker_id] = create_new_pane(command)
            else:
                self.workers[worker_id] = create_new_window("worker {}".format(worker_id), command)
        else:
            with open(os.devnull, 'w') as devnull:
                proc = subprocess.Popen(worker_config.argv, stdin=devnull, stdout=devnull, stderr=devnull)
                self.workers[worker_id] = proc
        self.max_worker_id += 1


    def start_server_in_thread(self, collected):
        self.server = Server(collected)
        self.server_thread = threading.Thread(target=self.server.serve, args=())
        self.server_thread.setDaemon(True)
        self.server_thread.start()

    def get_proxy(self):
        return xmlrpc_client.ServerProxy('http://{0}:{1}'.format(config.root.parallel.server_addr, self.server.port))

    def kill_workers(self):
        if config.root.tmux.enabled:
            for worker_pid in self.server.worker_pids:
                try:
                    os.kill(worker_pid, signal.SIGINT)
                except OSError as err:
                    if err.errno != errno.ESRCH:
                        raise
        else:
            for worker in self.workers.values():
                worker.send_signal(signal.SIGINT)

    def report_worker_error_logs(self):
        found_worker_errors_file = False
        for file_name in os.listdir(self.workers_error_dircetory):
            if file_name.startswith(config.root.parallel.worker_error_file):
                found_worker_errors_file = True
                with open(os.path.join(self.workers_error_dircetory, file_name)) as worker_file:
                    content = worker_file.readlines()
                    for line in content:
                        _logger.error("{}: {}", file_name, line)
        if not found_worker_errors_file:
            _logger.error("No worker error files were found")


    def wait_all_workers_to_connect(self):
        while self.server.state == ServerStates.WAIT_FOR_CLIENTS:
            if time.time() - self.server.start_time > config.root.parallel.worker_connect_timeout * self.workers_num:
                _logger.error("Timeout: Not all clients connected to server, terminating")
                _logger.error("Clients connected: {}".format(self.server.clients_last_communication_time.keys()))
                self.kill_workers()
                self.report_worker_error_logs()
                raise ParallelTimeout("Not all clients connected")
            time.sleep(TIME_BETWEEN_CHECKS)

    def check_worker_timed_out(self):
        for worker_id, last_connection_time in iteritems(self.server.get_workers_last_connection_time()):
            if time.time() - last_connection_time > config.root.parallel.communication_timeout_secs:
                _logger.error("Worker {} is down, terminating session".format(worker_id))
                self.report_worker_error_logs()
                if not config.root.tmux.enabled:
                    if self.workers[worker_id].poll() is None:
                        self.workers[worker_id].kill()
                elif not config.root.tmux.use_panes:
                    self.workers[worker_id].rename_window('stopped_client_{}'.format(worker_id))
                self.get_proxy().report_client_failure(worker_id)

    def check_no_requests_timeout(self):
        if time.time() - self.server.last_request_time > config.root.parallel.no_request_timeout:
            _logger.error("No request sent to server for {} seconds, terminating".format(config.root.parallel.no_request_timeout))
            if self.server.has_connected_clients():
                _logger.error("Clients that are still connected to server: {}".format(self.server.clients_last_communication_time.keys()))
            if self.server.has_more_tests():
                _logger.error("Number of unstarted tests: {}".format(self.server.unstarted_tests.qsize()))
            if self.server.executing_tests:
                _logger.error("Currently executed tests indexes: {}".format(self.server.executing_tests.values()))
            self.kill_workers()
            self.report_worker_error_logs()
            raise ParallelTimeout("No request sent to server for {} seconds".format(config.root.parallel.no_request_timeout))

    def is_process_running(self, pid):
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                return False
            else:
                raise
        return True

    def start(self):
        self.try_connect()
        if not config.root.parallel.server_port:
            self.args.extend(['--parallel-port', str(self.server.port)])
        try:
            for _ in range(self.workers_num):
                self.start_worker()
            self.wait_all_workers_to_connect()
            while self.server.should_wait_for_request():
                self.check_worker_timed_out()
                self.check_no_requests_timeout()
                time.sleep(TIME_BETWEEN_CHECKS)
        except INTERRUPTION_EXCEPTIONS:
            _logger.error("Server interrupted, stopping workers and terminating")
            self.get_proxy().session_interrupted()
            self.kill_workers()
            raise
        finally:
            if not config.root.tmux.enabled:
                for worker in self.workers.values():
                    worker.wait()
            else:
                for worker_pid in self.server.worker_pids:
                    for _ in range(10):
                        if not self.is_process_running(worker_pid):
                            break
                        else:
                            time.sleep(0.5)
            self.get_proxy().stop_serve()
            self.server_thread.join()
