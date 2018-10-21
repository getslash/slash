import threading
import logbook
import os
import pickle
import time
import collections
from six.moves import xmlrpc_client
from .server import NO_MORE_TESTS, PROTOCOL_ERROR, WAITING_FOR_CLIENTS
from ..exceptions import INTERRUPTION_EXCEPTIONS
from ..hooks import register
from ..ctx import context
from ..runner import run_tests
from ..conf import config
_logger = logbook.Logger(__name__)

class Worker(object):
    def __init__(self, client_id, session_id):
        super(Worker, self).__init__()
        self.client_id = client_id
        self.session_id = session_id
        self.server_addr = 'http://{}:{}'.format(config.root.parallel.server_addr, config.root.parallel.server_port)
        self.keepalive_server_addr = 'http://{}:{}'.format(config.root.parallel.server_addr, config.root.parallel.keepalive_port)
        self._stop_event = None
        self._watchdog_thread = None

    def keep_alive(self, stop_event):
        proxy = xmlrpc_client.ServerProxy(self.keepalive_server_addr)
        while not stop_event.is_set():
            proxy.keep_alive(self.client_id)
            stop_event.wait(1)

    def warning_added(self, warning):
        try:
            warning = pickle.dumps(warning)
            self.client.report_warning(self.client_id, warning)
        except (pickle.PicklingError, TypeError):
            _logger.error("Failed to pickle warning. Message: {}, File: {}, Line: {}",
                          warning.message, warning.filename, warning.lineno, extra={'capture': False})

    def error_added(self, error, result):
        if result.is_global_result():
            self.client.report_session_error("Session error in client id {}: {}".format(self.client_id, error.message))

    def write_to_error_file(self, msg):
        try:
            file_name = "{}-{}.log".format(config.root.parallel.worker_error_file, self.client_id)
            worker_error_file = os.path.join(config.root.parallel.workers_error_dir, file_name)
            with open(worker_error_file, 'a') as error_file:
                error_file.write(msg)
        except OSError as err:
            _logger.error("Failed to write to worker error file, error: {}", err, extra={'capture': False})

    def connect_to_server(self):
        try:
            self.client = xmlrpc_client.ServerProxy(self.server_addr, allow_none=True)
            self.client.connect(self.client_id, os.getpid())
            self._stop_event = threading.Event()
            self._watchdog_thread = threading.Thread(target=self.keep_alive, args=(self._stop_event,))
            self._watchdog_thread.setDaemon(True)
            self._watchdog_thread.start()
        except OSError as err:
            self.write_to_error_file("Failed to connect to server, error: {}".format(str(err)))

    def _stop_keepalive_thread(self):
        if self._stop_event is not None and not self._stop_event.is_set():
            self._stop_event.set()
            self._watchdog_thread.join()

    def start_execution(self, app, collected_tests):
        if os.getpid() != os.getpgid(0):
            os.setsid()
        register(self.warning_added)
        register(self.error_added)
        collection = [(test.__slash__.file_path,
                      test.__slash__.function_name,
                      test.__slash__.variation.dump_variation_dict()) for test in collected_tests]
        if not self.client.validate_collection(self.client_id, sorted(collection)):
            _logger.error("Collections of worker id {} and master don't match, worker terminates", self.client_id,
                          extra={'capture': False})
            self._stop_keepalive_thread()
            self.client.disconnect(self.client_id)
            return

        should_stop = False
        signatures_dict = collections.defaultdict(set)
        for index, test in enumerate(collection):
            signatures_dict[test].add(index)
        with app.session.get_started_context():
            try:
                while not should_stop:
                    test_entry = self.client.get_test(self.client_id)
                    if test_entry == WAITING_FOR_CLIENTS:
                        _logger.debug("Worker_id {} recieved waiting_for_clients, sleeping", self.client_id)
                        time.sleep(0.05)
                    elif test_entry == PROTOCOL_ERROR:
                        _logger.error("Worker_id {} recieved protocol error message, terminating", self.client_id,
                                      extra={'capture': False})
                        break
                    elif test_entry == NO_MORE_TESTS:
                        _logger.debug("Got NO_MORE_TESTS, Client {} disconnecting", self.client_id)
                        break
                    else:
                        index = signatures_dict[tuple(test_entry[0])].pop()
                        test = collected_tests[index]
                        context.session.current_parallel_test_index = test_entry[1]
                        run_tests([test])
                        result = context.session.results[test]
                        _logger.debug("Client {} finished test, sending results", self.client_id)
                        ret = self.client.finished_test(self.client_id, result.serialize())
                        if ret == PROTOCOL_ERROR:
                            _logger.error("Worker_id {} recieved protocol error message, terminating", self.client_id,
                                          extra={'capture': False})
                            should_stop = True
            except INTERRUPTION_EXCEPTIONS:
                self.write_to_error_file("Worker interrupted while executing test")
                _logger.error("Worker interrupted while executing test", extra={'capture': False})
                raise
            except Exception as err:
                self.write_to_error_file(str(err))
                raise
            else:
                context.session.mark_complete()
                context.session.initiate_cleanup()
                self._stop_keepalive_thread()
                self.client.disconnect(self.client_id)
            finally:
                context.session.initiate_cleanup()
                self._stop_keepalive_thread()
