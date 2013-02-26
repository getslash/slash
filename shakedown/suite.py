from .interfaces import Activatable
from .ctx import ctx

class Suite(Activatable):
    def activate(self):
        assert ctx.suite is None
        ctx.suite = self
    def deactivate(self):
        ctx.suite = None
