import itertools

class IDSpace(object):
    def __init__(self, base):
        super(IDSpace, self).__init__()
        if not base.endswith(":"):
            base += ":"
        self._allocator = (base + str(i) for i in itertools.count(1))
    def allocate(self):
        return next(self._allocator)
