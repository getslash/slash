import uuid
from contextlib import contextmanager
from .. import ctx, hooks, log
from ..exception_handling import handling_exceptions
from ..interfaces import Activatable
from .result import SessionResults
from ..utils.id_space import IDSpace
from ..warnings import SessionWarnings

class Session(Activatable):
    def __init__(self):
        super(Session, self).__init__()
        self.id = "{0}:0".format(uuid.uuid1())
        self.id_space = IDSpace(self.id)
        self._complete = False
        self._context = None
        self.warnings = SessionWarnings()
        self.logging = log.SessionLogging(self)
        #: an aggregate result summing all test results and the global result
        self.results = SessionResults()

    def activate(self):
        assert self._context is None
        self._context = _session_context(self)
        with handling_exceptions():
            self._context.__enter__()

    def deactivate(self):
        self.results.global_result.mark_finished()
        with handling_exceptions():
            self._context.__exit__(None, None, None)

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
            hooks.session_start()
            hooks.after_session_start()
            try:
                yield
            finally:
                hooks.session_end()
    finally:
        ctx.pop_context()

