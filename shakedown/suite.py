from .interfaces import Activatable
from .ctx import context
from .utils.id_space import IDSpace
from .result import AggregatedResult
from .result import Result
from six import itervalues # pylint: disable=F0401

class Suite(Activatable):
    def __init__(self):
        super(Suite, self).__init__()
        self.id = self.id_space = None
        self._results = {}
        self.result = AggregatedResult(self.iter_results)
    def activate(self):
        assert context.suite is None
        self.id = context.session.id_space.allocate()
        self.id_space = IDSpace(self.id)
        context.suite = self
        context.session.add_suite(self)
    def deactivate(self):
        context.suite = None
    def get_result(self, test):
        return self._results[test.__shakedown__.id]
    def create_result(self, test):
        assert test.__shakedown__.id not in self._results
        returned = Result()
        self._results[test.__shakedown__.id] = returned
        return returned
    def iter_results(self):
        return itervalues(self._results)
