from .interfaces import Activatable
from . import ctx

class Session(Activatable):
    def activate(self):
        assert ctx.ctx.session is None
        ctx.ctx.session = self
    def deactivate(self):
        ctx.ctx.session = None
