from . import ctx
from .interfaces import Activatable
from .result import AggregatedResult
from .utils.id_space import IDSpace
from . import hooks
import uuid

class Session(Activatable):
    def __init__(self):
        super(Session, self).__init__()
        self.id = self.id_space = None
        self.result = AggregatedResult(self._iter_suite_results)
        self._suites = []
    def _iter_suite_results(self):
        for suite in self._suites:
            yield suite.result
    def activate(self):
        assert ctx.context.session is None
        ctx.push_context()
        ctx.context.session = self
        self.id = str(uuid.uuid1())
        self.id_space = IDSpace(self.id)
        hooks.session_start()
    def deactivate(self):
        hooks.session_end()
        ctx.pop_context()
    def add_suite(self, suite):
        self._suites.append(suite)
