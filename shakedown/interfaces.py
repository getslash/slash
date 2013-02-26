class Activatable(object):
    def activate(self):
        raise NotImplementedError() # pragma: no cover
    def deactivate(self):
        raise NotImplementedError() # pragma: no cover
    def __enter__(self):
        self.activate()
        return self
    def __exit__(self, *_, **__):
        self.deactivate()

