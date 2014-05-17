import time
import uuid
from contextlib import contextmanager


from .. import ctx, hooks, log
from ..exception_handling import handling_exceptions
from ..interfaces import Activatable
from ..reporting.null_reporter import NullReporter
from ..utils.id_space import IDSpace
from ..warnings import SessionWarnings
from .result import SessionResults


class Session(Activatable):

    duration = start_time = end_time = None

    def __init__(self, reporter=None):
        super(Session, self).__init__()
        self.id = "{0}_0".format(uuid.uuid1())
        self.id_space = IDSpace(self.id)
        self._complete = False
        self._context = None
        self.warnings = SessionWarnings()
        self.logging = log.SessionLogging(self)
        #: an aggregate result summing all test results and the global result
        self.results = SessionResults(self)
        if reporter is None:
            reporter = NullReporter()
        self.reporter = reporter

    def activate(self):
        self.start_time = time.time()
        assert self._context is None
        self._context = _session_context(self)
        with handling_exceptions():
            self._context.__enter__()
        self.reporter.report_session_start(self)

    def deactivate(self):
        self.results.global_result.mark_finished()
        with handling_exceptions():
            self._context.__exit__(None, None, None)
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.reporter.report_session_end(self)

    def mark_complete(self):
        self._complete = True

    def is_complete(self):
        return self._complete


@contextmanager
def _session_context(session):
    assert ctx.context.session is None
    ctx.push_context()
    ctx.context.session = session
    try:
        with session.logging.get_session_logging_context():
            hooks.session_start()  # pylint: disable=no-member
            hooks.after_session_start()  # pylint: disable=no-member
            try:
                yield
            finally:
                hooks.session_end()  # pylint: disable=no-member
    finally:
        ctx.pop_context()
