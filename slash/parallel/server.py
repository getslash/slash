import copy
import logbook
import functools
import time
from enum import Enum
from six.moves import queue
from six.moves import xmlrpc_server
from ..utils.python import unpickle
from .. import log
from ..ctx import context
from ..runner import _get_test_context
from .. import hooks
from ..conf import config
_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')

NO_MORE_TESTS = "NO_MORE_TESTS"
PROTOCOL_ERROR = "PROTOCOL_ERROR"
WAITING_FOR_CLIENTS = "WAITING_FOR_CLIENTS"

class ServerStates(Enum):
    NOT_INITIALIZED = 1
    WAIT_FOR_CLIENTS = 2
    SERVE_TESTS = 3
    STOP_TESTS_SERVING = 4
    STOP_SERVE = 5

def server_func(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        time_now = time.time()
        client_id = kwargs.pop('client_id', args[1])
        self.clients_last_communication_time[client_id] = self.last_request_time = time_now
        return func(*args)  # pylint: disable=not-callable
    return wrapper

class Server(object):
    def __init__(self, tests):
        super(Server, self).__init__()
        self.host = config.root.parallel.server_addr
        self.interrupted = False
        self.state = ServerStates.NOT_INITIALIZED
        self.port = None
        self.tests = tests
        self.worker_session_ids = []
        self.executing_tests = {}
        self.finished_tests = []
        self.unstarted_tests = queue.Queue()
        self.last_request_time = time.time()
        self.worker_pids = []
        for i in range(len(tests)):
            self.unstarted_tests.put(i)
        self.clients_last_communication_time = {}
        self.collection = [[test.__slash__.file_path, test.__slash__.function_name, test.__slash__.variation.id] for test in self.tests]

    def get_workers_last_connection_time(self):
        return copy.deepcopy(self.clients_last_communication_time)

    def _has_unstarted_tests(self):
        return not self.unstarted_tests.empty()

    def _has_connected_clients(self):
        return len(self.clients_last_communication_time) > 0

    def has_more_tests(self):
        return len(self.finished_tests) < len(self.tests)

    def report_client_failure(self, client_id):
        self.clients_last_communication_time.pop(client_id)
        test_index = self.executing_tests.get(client_id, None)
        if test_index is not None:
            _logger.error("Worker {} interrupted while executing test {}".format(client_id, self.tests[test_index].__slash__.address))
            with _get_test_context(self.tests[test_index]) as result:
                result.mark_interrupted()
                self.finished_tests.append(test_index)
        self.state = ServerStates.STOP_TESTS_SERVING
        self._mark_unrun_tests()

    def _mark_unrun_tests(self):
        while self._has_unstarted_tests():
            test_index = self.unstarted_tests.get()
            with _get_test_context(self.tests[test_index]):
                pass
            self.finished_tests.append(test_index)

    @server_func
    def keep_alive(self, client_id):
        _logger.debug("Client_id {} sent keep_alive".format(client_id))

    @server_func
    def connect(self, client_id, client_pid):
        _logger.notice("Client_id {} connected".format(client_id))
        client_session_id = '{}_{}'.format(context.session.id.split('_')[0], client_id)
        context.session.logging.create_worker_symlink("worker_{}".format(client_id), client_session_id)
        hooks.worker_connected(session_id=client_session_id)  # pylint: disable=no-member
        self.worker_session_ids.append(client_session_id)
        self.worker_pids.append(client_pid)
        self.executing_tests[client_id] = None
        if len(self.clients_last_communication_time) >= config.root.parallel.num_workers:
            self.state = ServerStates.SERVE_TESTS

    @server_func
    def validate_collection(self, client_id, client_collection):
        if not self.collection == client_collection:
            _logger.error("Client_id {} sent wrong collection".format(client_id))
            return False
        return True

    @server_func
    def disconnect(self, client_id):
        _logger.notice("Client {} sent disconnect".format(client_id))
        self.clients_last_communication_time.pop(client_id)
        self.state = ServerStates.STOP_TESTS_SERVING

    @server_func
    def get_test(self, client_id):
        if not self.executing_tests[client_id] is None:
            _logger.error("Client_id {} requested new test without sending former result".format(client_id))
            return PROTOCOL_ERROR
        if self.state == ServerStates.STOP_TESTS_SERVING:
            return NO_MORE_TESTS
        elif self.state == ServerStates.WAIT_FOR_CLIENTS:
            return WAITING_FOR_CLIENTS
        elif self.state == ServerStates.SERVE_TESTS and self._has_unstarted_tests():
            test_index = self.unstarted_tests.get()
            test = self.tests[test_index]
            self.executing_tests[client_id] = test_index
            _logger.notice("#{}: {}, Client_id: {}", test_index + 1, test.__slash__.address, client_id, extra={'to_error_log': 1})
            return test_index
        else:
            _logger.debug("No unstarted tests, sending end to client_id {}".format(client_id))
            self.state = ServerStates.STOP_TESTS_SERVING
            return NO_MORE_TESTS

    @server_func
    def finished_test(self, client_id, result_dict):
        _logger.debug("Client_id {} finished_test".format(client_id))
        test_index = self.executing_tests.get(client_id, None)
        if test_index is not None:
            self.finished_tests.append(test_index)
            self.executing_tests[client_id] = None
            with _get_test_context(self.tests[test_index]) as result:
                result.deserialize(result_dict)
                context.session.reporter.report_test_end(self.tests[test_index], result)
                if not result.is_success(allow_skips=True) and config.root.run.stop_on_error:
                    _logger.debug("Stopping (run.stop_on_error==True)")
                    self.state = ServerStates.STOP_TESTS_SERVING
                    self._mark_unrun_tests()
        else:
            _logger.error(
                "finished_test request from client_id {} with index {}, but no test is mapped to this worker".format(client_id, test_index))
            return PROTOCOL_ERROR

    def stop_serve(self):
        self.state = ServerStates.STOP_SERVE

    @server_func
    def report_warning(self, client_id, pickled_warning):
        _logger.notice("Client_id {} sent warning".format(client_id))
        try:
            warning = unpickle(pickled_warning)
            context.session.warnings.add(warning)
        except TypeError:
            _logger.error('Error when deserializing warning, not adding it')

    def should_wait_for_request(self):
        return  self._has_connected_clients() or self.has_more_tests()

    def serve(self):
        try:
            server = xmlrpc_server.SimpleXMLRPCServer((self.host, config.root.parallel.server_port), allow_none=True, logRequests=False)
            self.port = server.server_address[1]
            self.state = ServerStates.WAIT_FOR_CLIENTS
            server.register_instance(self)
            _logger.debug("Starting server loop")
            while self.state != ServerStates.STOP_SERVE:
                server.handle_request()
            if not self.interrupted:
                context.session.mark_complete()
            _logger.trace('Session finished. is_success={0} has_skips={1}',
                          context.session.results.is_success(allow_skips=True), bool(context.session.results.get_num_skipped()))
            _logger.debug("Exiting server loop")
        finally:
            server.server_close()
