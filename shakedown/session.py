from . import ctx
from .interfaces import Activatable
from .result import Result
from .utils.id_space import IDSpace
import uuid

class Session(Activatable):
    def __init__(self):
        super(Session, self).__init__()
        self.id = self.id_space = None
        self._results = {}
    def activate(self):
        assert ctx.ctx.session is None
        ctx.ctx.session = self
        self.id = str(uuid.uuid1())
        self.id_space = IDSpace(self.id)
    def deactivate(self):
        ctx.ctx.session = None
    def get_result(self, test):
        return self._results[test.__shakedown__.id]
    def create_result(self, test):
        assert test.__shakedown__.id not in self._results
        returned = Result()
        self._results[test.__shakedown__.id] = returned
        return returned

