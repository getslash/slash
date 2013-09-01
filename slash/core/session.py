import uuid
from contextlib import contextmanager
from .. import ctx, hooks, log
from .._compat import OrderedDict
from ..exception_handling import handling_exceptions
from ..interfaces import Activatable
from .result import Result
from .result import SessionResult
from ..utils.id_space import IDSpace
from ..warnings import SessionWarnings

class Session(Activatable):
    def __init__(self):
        super(Session, self).__init__()
        self.id = "{0}:0".format(uuid.uuid1())
        self.id_space = IDSpace(self.id)
        self._complete = False
        self._context = None
        self._results = OrderedDict()
        self.warnings = SessionWarnings()
        self.logging = log.SessionLogging(self)
        #: an aggregate result summing all test results and the global result
        self.result = SessionResult(self._results)

    def create_result(self, test):
        assert test.__slash__.id not in self._results
        returned = Result(test.__slash__)
        self._results[test.__slash__.id] = returned
        return returned

    def get_result(self, test):
        if test.__slash__ is None:
            raise LookupError("Could not find result for {0}".format(test))
        return self._results[test.__slash__.id]

    def activate(self):
        assert self._context is None
        self._context = _session_context(self)
        with handling_exceptions():
            self._context.__enter__()

    def deactivate(self):
        self.result.global_result.mark_finished()
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
            try:
                yield
            finally:
                hooks.session_end()
    finally:
        ctx.pop_context()

