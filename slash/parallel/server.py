import copy
import logbook
import functools
from six.moves import queue
from datetime import datetime
from six.moves import xmlrpc_server
from ..utils.python import unpickle
from .. import log
from ..ctx import context
from ..runner import _get_test_context
from collections import defaultdict
from .. import hooks
from ..conf import config

_logger = logbook.Logger(__name__)
log.set_log_color(_logger.name, logbook.NOTICE, 'blue')

FINISHED_ALL_TESTS = "NO_MORE_TESTS"
PROTOCOL_ERROR = "PROTOCOL_ERROR"

def server_func(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        client_id = kwargs.pop('client_id', args[1])
        self.clients_last_communication_time[client_id] = datetime.now()
        return func(*args)  # pylint: disable=not-callable
    return wrapper

class Server(object):
    def __init__(self, tests):
        super(Server, self).__init__()
        self.host = config.root.parallel.server_addr
        self.port = None
        self.should_stop_on_error = config.root.run.stop_on_error
        self.tests = tests
        self.stop_on_error_and_error_found = False
        self.is_initialized = False
        self.worker_session_ids = []
        self.executing_tests = {}
        self.finished_tests = []
        self.unstarted_tests = queue.Queue()
        self.should_stop = False
        for i in range(len(tests)):
            self.unstarted_tests.put(i)
        self.tests_restart_count = defaultdict(int)
        self.clients_last_communication_time = {}
        self.collection = [[test.__slash__.file_path, test.__slash__.function_name, test.__slash__.variation.id] for test in self.tests]

    def get_workers_last_connection_time(self):
        return copy.deepcopy(self.clients_last_communication_time)

    def _has_unstarted_tests(self):
        return not self.unstarted_tests.empty()

    def _has_unfinished_tests(self):
        return len(self.finished_tests) < len(self.tests)

    def _has_connected_clients(self):
        return len(self.clients_last_communication_time) > 0

    def has_more_tests(self):
        return self._has_unfinished_tests() and not self.stop_on_error_and_error_found

    def report_client_failure(self, client_id):
        self.clients_last_communication_time.pop(client_id)
        test_index = self.executing_tests.get(client_id, None)
        if test_index is not None:
            _logger.error("Worker {} interrupted while executing test {}".format(client_id, self.tests[test_index].__slash__.address))
            with _get_test_context(self.tests[test_index]) as result:
                result.mark_interrupted()
                self.finished_tests.append(test_index)

    def _mark_unrun_tests(self):
        while self._has_unstarted_tests():
            test_index = self.unstarted_tests.get()
            with _get_test_context(self.tests[test_index]):
                pass
            self.finished_tests.append(test_index)

    def stop_server(self):
        self.should_stop = True

    @server_func
    def keep_alive(self, client_id):
        _logger.debug("Client_id {} sent keep_alive".format(client_id))

    @server_func
    def connect(self, client_id, session_id):
        _logger.notice("Client_id {} connected with session_id {}".format(client_id, session_id))
        context.session.logging.create_worker_symlink("worker_{}".format(client_id), session_id)
        hooks.worker_connected(session_id=session_id)  # pylint: disable=no-member
        self.worker_session_ids.append(session_id)
        self.executing_tests[client_id] = None

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

    @server_func
    def get_test(self, client_id):
        if not self.executing_tests[client_id] is None:
            _logger.error("Client_id {} requested new test without sending former result".format(client_id))
            return PROTOCOL_ERROR
        if self._has_unstarted_tests():
            test_index = self.unstarted_tests.get()
            test = self.tests[test_index]
            self.executing_tests[client_id] = test_index
            _logger.notice("#{}: {}, Client_id: {}", test_index, test.__slash__.address, client_id, extra={'to_error_log': 1})
            return test_index
        else:
            _logger.debug("No unstarted tests, sending end to client_id {}".format(client_id))
            return FINISHED_ALL_TESTS

    @server_func
    def finished_test(self, client_id, result_dict):
        _logger.notice("Client_id {} finished_test".format(client_id))
        test_index = self.executing_tests.get(client_id, None)
        if test_index is not None:
            self.finished_tests.append(test_index)
            self.executing_tests[client_id] = None
            with _get_test_context(self.tests[test_index]) as result:
                result.deserialize(result_dict)
                context.session.reporter.report_test_end(self.tests[test_index], result)
                if not result.is_success(allow_skips=True) and self.should_stop_on_error:
                    _logger.debug("Stopping (run.stop_on_error==True)")
                    self.stop_on_error_and_error_found = True
                    self._mark_unrun_tests()
        else:
            _logger.error(
                "finished_test request from client_id {} with index {}, but no test is mapped to this worker".format(client_id, test_index))
            return PROTOCOL_ERROR

    @server_func
    def report_warning(self, client_id, pickled_warning):
        _logger.notice("Client_id {} sent warning".format(client_id))
        try:
            warning = unpickle(pickled_warning)
            context.session.warnings.add(warning)
        except TypeError:
            _logger.error('Error when deserializing warning, not adding it')

    def serve(self):
        try:
            server = xmlrpc_server.SimpleXMLRPCServer((self.host, config.root.parallel.server_port), allow_none=True, logRequests=False)
            self.port = server.server_address[1]
            self.is_initialized = True
            server.register_instance(self)
            _logger.debug("Starting server loop")
            while not self.should_stop and (self._has_connected_clients() or self.has_more_tests()):
                server.handle_request()
            if not self.stop_on_error_and_error_found:
                context.session.mark_complete()
            _logger.trace('Session finished. is_success={0} has_skips={1}',
                          context.session.results.is_success(allow_skips=True), bool(context.session.results.get_num_skipped()))
            _logger.debug("Exiting server loop")
        finally:
            server.server_close()
