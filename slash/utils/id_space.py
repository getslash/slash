import itertools

_ID_SEPARATOR = "_"


class IDSpace:
    def __init__(self, base):
        super().__init__()
        if not base.endswith(_ID_SEPARATOR):
            base += _ID_SEPARATOR
        self._allocator = (base + str(i) for i in itertools.count(1))

    def allocate(self):
        return next(self._allocator)
