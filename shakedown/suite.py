from .interfaces import Activatable

class Suite(Activatable):
    def __init__(self):
        super(Suite, self).__init__()
    def activate(self):
        pass
    def deactivate(self):
        pass

