import os
import time
import logbook
import threading
from tempfile import mkdtemp
from  six.moves import xmlrpc_client
from .. import log
from ..exceptions import INTERRUPTION_EXCEPTIONS, ParallelServerIsDown, ParallelTimeout
from ..conf import config
from .server import Server, ServerStates, KeepaliveServer
from .worker_configuration import TmuxWorkerConfiguration, ProcessWorkerConfiguration

_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')

TIME_BETWEEN_CHECKS = 2
MAX_CONNECTION_RETRIES = 200

def get_xmlrpc_proxy(address, port):
    return xmlrpc_client.ServerProxy('http://{}:{}'.format(address, port))


class ParallelManager(object):
    def __init__(self, args):
        super(ParallelManager, self).__init__()
        self.server = None
        self.workers_error_dircetory = mkdtemp()
        self.args = args
        self.workers_num = config.root.parallel.num_workers
        self.workers = {}
        self.server_thread = None
        self.keepalive_server = None
        self.keepalive_server_thread = None
        self._create_workers()

    def _create_workers(self):
        for index in range(1, self.workers_num+1):
            _logger.debug("Creating worker number {}", index)
            index_str = str(index)
            worker_cls = TmuxWorkerConfiguration if config.root.tmux.enabled else ProcessWorkerConfiguration
            self.workers[index_str] = worker_cls(self.args, index_str)

    def try_connect(self):
        for _ in range(MAX_CONNECTION_RETRIES):
            if self.server.state != ServerStates.NOT_INITIALIZED and self.keepalive_server.state != ServerStates.NOT_INITIALIZED:
                return
            time.sleep(0.1)
        raise ParallelServerIsDown("Cannot connect to XML_RPC server")

    def start_server_in_thread(self, collected):
        self.server = Server(collected)
        self.server_thread = threading.Thread(target=self.server.serve, args=())
        self.server_thread.setDaemon(True)
        self.server_thread.start()
        self.keepalive_server = KeepaliveServer()
        self.keepalive_server_thread = threading.Thread(target=self.keepalive_server.serve, args=())
        self.keepalive_server_thread.setDaemon(True)
        self.keepalive_server_thread.start()

    def kill_workers(self):
        for worker in list(self.workers.values()):
            worker.kill()

    def report_worker_error_logs(self):
        found_worker_errors_file = False
        for file_name in os.listdir(self.workers_error_dircetory):
            if file_name.startswith(config.root.parallel.worker_error_file):
                found_worker_errors_file = True
                with open(os.path.join(self.workers_error_dircetory, file_name)) as worker_file:
                    content = worker_file.readlines()
                    for line in content:
                        _logger.error("{}: {}", file_name, line, extra={'capture': False})
        if not found_worker_errors_file:
            _logger.error("No worker error files were found", extra={'capture': False})

    def handle_error(self, failure_message):
        _logger.error(failure_message, extra={'capture': False})
        self.kill_workers()
        self.report_worker_error_logs()
        get_xmlrpc_proxy(config.root.parallel.server_addr, self.server.port).report_session_error(failure_message)
        raise ParallelTimeout(failure_message)

    def wait_all_workers_to_connect(self):
        while self.server.state == ServerStates.WAIT_FOR_CLIENTS:
            if time.time() - self.server.start_time > config.root.parallel.worker_connect_timeout * self.workers_num:
                self.handle_error("Timeout: Not all clients connected to server, terminating.\n\
                                   Clients connected: {}".format(self.server.connected_clients))
            time.sleep(TIME_BETWEEN_CHECKS)

    def check_worker_timed_out(self):
        workers_last_connection_time = self.keepalive_server.get_workers_last_connection_time()
        for worker_id in self.server.get_connected_clients():
            worker_last_connection_time = workers_last_connection_time.get(worker_id, None)
            if worker_last_connection_time is None: #worker keepalive thread didn't started yet
                continue
            if time.time() - worker_last_connection_time > config.root.parallel.communication_timeout_secs:
                _logger.error("Worker {} is down, terminating session", worker_id, extra={'capture': False})
                self.report_worker_error_logs()
                self.workers[worker_id].handle_timeout()
                get_xmlrpc_proxy(config.root.parallel.server_addr, self.server.port).report_client_failure(worker_id)

    def check_no_requests_timeout(self):
        if time.time() - self.keepalive_server.last_request_time > config.root.parallel.no_request_timeout:
            _logger.error("No request sent to server for {} seconds, terminating",
                          config.root.parallel.no_request_timeout, extra={'capture': False})
            if self.server.has_connected_clients():
                _logger.error("Clients that are still connected to server: {}",
                              self.server.connected_clients, extra={'capture': False})
            if self.server.has_more_tests():
                _logger.error("Number of unstarted tests: {}", len(self.server.get_unstarted_tests()),
                              extra={'capture': False})
            if self.server.executing_tests:
                _logger.error("Currently executed tests indexes: {}", self.server.executing_tests.values(),
                              extra={'capture': False})
            self.handle_error("No request sent to server for {} seconds, terminating".format(config.root.parallel.no_request_timeout))

    def start(self):
        self.try_connect()
        try:
            for worker in list(self.workers.values()):
                worker.start()
            self.wait_all_workers_to_connect()
            while self.server.should_wait_for_request():
                self.check_worker_timed_out()
                self.check_no_requests_timeout()
                time.sleep(TIME_BETWEEN_CHECKS)
        except INTERRUPTION_EXCEPTIONS:
            _logger.error("Server interrupted, stopping workers and terminating", extra={'capture': False})
            get_xmlrpc_proxy(config.root.parallel.server_addr, self.server.port).session_interrupted()
            self.kill_workers()
            raise
        finally:
            for worker in list(self.workers.values()):
                worker.wait_to_finish()

            get_xmlrpc_proxy(config.root.parallel.server_addr, self.server.port).stop_serve()
            get_xmlrpc_proxy(config.root.parallel.server_addr, self.keepalive_server.port).stop_serve()
            self.server_thread.join()
            self.keepalive_server_thread.join()
