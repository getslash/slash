import itertools
import sys
import socket
import time
import uuid
from contextlib import contextmanager
from ..conf import config
from .. import ctx, hooks, log, exceptions
from .cleanup_manager import CleanupManager
from ..exception_handling import handling_exceptions
from ..interfaces import Activatable
from ..reporting.null_reporter import NullReporter
from ..utils.id_space import IDSpace
from ..utils.interactive import notify_if_slow_context
from ..warnings import SessionWarnings
from .fixtures.fixture_store import FixtureStore
from .result import SessionResults
from .scope_manager import ScopeManager


class Session(Activatable):
    """ Represents a slash session
    """

    start_time = end_time = host_fqdn = host_name = None

    def __init__(self, reporter=None, console_stream=None):
        super(Session, self).__init__()
        self.parent_session_id = config.root.parallel.parent_session_id
        self.id = "{0}_0".format(uuid.uuid1()) if not self.parent_session_id else \
                    "{}_{}".format(self.parent_session_id.split('_')[0], config.root.parallel.worker_id)
        self.id_space = IDSpace(self.id)
        self.test_index_counter = itertools.count()
        self.scope_manager = ScopeManager(self)
        self._started = False
        self._complete = False
        self._active = False
        self._active_context = None
        self.parallel_manager = None
        self.fixture_store = FixtureStore()
        self.warnings = SessionWarnings()
        self.logging = log.SessionLogging(self, console_stream=console_stream)
        self.current_parallel_test_index = None
        #: an aggregate result summing all test results and the global result
        self.results = SessionResults(self)
        if reporter is None:
            reporter = NullReporter()
        self.reporter = reporter
        self.cleanups = CleanupManager()

        self._skip_exc_types = (exceptions.SkipTest,)

    def register_skip_exception(self, exc_type):
        self._skip_exc_types += (exc_type,)

    def get_skip_exception_types(self):
        return self._skip_exc_types

    def has_children(self):
        return not self.parallel_manager is None

    @property
    def started(self):
        return self._started

    def activate(self):
        assert not self._active, 'Attempted to activate an already-active session'
        with handling_exceptions():
            ctx.push_context()
            assert ctx.context.session is None
            assert ctx.context.result is None
            ctx.context.session = self
            ctx.context.result = self.results.global_result
            self.results.global_result.mark_started()
            self._logging_context = self.logging.get_session_logging_context()
            self._logging_context.__enter__()

            self._warning_capture_context = self.warnings.capture_context()
            self._warning_capture_context.__enter__()
        self._active = True

    def deactivate(self):
        assert self._active, 'Session not active'
        self._active = False
        self.results.global_result.mark_finished()

        exc_info = sys.exc_info()

        self._warning_capture_context.__exit__(*exc_info) # pylint: disable=no-member
        self._warning_capture_context = None

        self._logging_context.__exit__(*exc_info) # pylint: disable=no-member
        self._logging_context = None
        self.results.global_result.mark_finished()
        ctx.pop_context()

    @property
    def duration(self):
        if self.end_time is not None:
            return self.end_time - self.start_time
        curr_time = time.time()
        return (self.end_time or curr_time) - (self.start_time or curr_time)

    @contextmanager
    def get_started_context(self):
        if self.host_fqdn is None:
            type(self).host_fqdn = socket.getfqdn()
        self.host_name = self.host_fqdn.split('.')[0]
        self.start_time = time.time()
        self.cleanups.push_scope('session-global')
        session_start_called = False
        try:
            with handling_exceptions():
                with notify_if_slow_context("Initializing session..."):
                    hooks.before_session_start()  # pylint: disable=no-member
                    hooks.session_start()  # pylint: disable=no-member
                    session_start_called = True
                    hooks.after_session_start()  # pylint: disable=no-member
            self._started = True
            yield
        except exceptions.INTERRUPTION_EXCEPTIONS:
            hooks.session_interrupt() # pylint: disable=no-member
            raise
        finally:
            self._started = False
            self.end_time = time.time()

            with handling_exceptions():
                self.cleanups.pop_scope('session-global')

            if session_start_called:
                with handling_exceptions():
                    hooks.session_end()  # pylint: disable=no-member
            self.reporter.report_session_end(self)

    def mark_complete(self):
        self._complete = True

    def is_complete(self):
        return self._complete

    _total_num_tests = 0

    def get_total_num_tests(self):
        """Returns the total number of tests expected to run in this session
        """
        return self._total_num_tests

    def increment_total_num_tests(self, increment):
        self._total_num_tests += increment
