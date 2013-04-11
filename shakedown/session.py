from . import ctx
from . import hooks
from . import log
from .interfaces import Activatable
from .result import AggregatedResult
from .utils.id_space import IDSpace
from contextlib import contextmanager
import uuid

class Session(Activatable):
    def __init__(self):
        super(Session, self).__init__()
        self.id = str(uuid.uuid1())
        self.id_space = IDSpace(self.id)
        self.result = AggregatedResult(self._iter_suite_results)
        self._suites = []
        self._context = None
    def _iter_suite_results(self):
        for suite in self._suites:
            yield suite.result
    def iter_suites(self):
        return iter(self._suites)
    def activate(self):
        assert self._context is None
        self._context = _session_context(self)
        self._context.__enter__()
    def deactivate(self):
        self._context.__exit__(None, None, None)
    def add_suite(self, suite):
        self._suites.append(suite)

@contextmanager
def _session_context(session):
    assert ctx.context.session is None
    ctx.push_context()
    ctx.context.session = session
    try:
        with log.get_session_logging_context():
            hooks.session_start()
            try:
                yield
            finally:
                hooks.session_end()
    finally:
        ctx.pop_context()

