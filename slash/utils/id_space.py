import itertools

_ID_SEPARATOR = "_"

class IDSpace(object):
    def __init__(self, base):
        super(IDSpace, self).__init__()
        if not base.endswith(_ID_SEPARATOR):
            base += _ID_SEPARATOR
        self._allocator = (base + str(i) for i in itertools.count(1))
    def allocate(self):
        return next(self._allocator)
