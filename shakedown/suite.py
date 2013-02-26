from .interfaces import Activatable
from .ctx import ctx
from .utils.id_space import IDSpace

class Suite(Activatable):
    def __init__(self):
        super(Suite, self).__init__()
        self.id = self.id_space = None
    def activate(self):
        assert ctx.suite is None
        self.id = ctx.session.id_space.allocate()
        self.id_space = IDSpace(self.id)
        ctx.suite = self
    def deactivate(self):
        ctx.suite = None
