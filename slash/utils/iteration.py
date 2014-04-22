_NOTHING = object()
_END = object()

class PeekableIterator(object):
    """An iterator wrapper which allows peeking into the next element"""
    def __init__(self, iterator):
        super(PeekableIterator, self).__init__()
        self._iterator = iter(iterator)
        self._peeked = _NOTHING

    def __iter__(self):
        return self

    def next(self):
        if self._peeked is not _NOTHING:
            returned = self._peeked
            self._peeked = _NOTHING
            if returned is _END:
                raise StopIteration()
            return returned
        return next(self._iterator)
    __next__ = next

    def peek_or_none(self):
        if self.has_next():
            return self.peek()
        return None

    def peek(self):
        if self._peeked is _NOTHING:
            self._peeked = next(self._iterator, _END)
        if self._peeked is _END:
            raise StopIteration()
        return self._peeked

    def has_next(self):
        try:
            self.peek()
        except StopIteration:
            return False
        return True
