import itertools

from .._compat import itervalues

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


def iteration(iterable):
    try:
        last_counter0 = len(iterable) - 1
    except (ValueError, TypeError):
        last_counter0 = None

    for index, element in enumerate(iterable):

        yield Iteration(element, counter0=index, counter1=index + 1, first=(index == 0), last_counter0=last_counter0)


class Iteration(object):

    def __init__(self, element, counter0, counter1, first, last_counter0=None):
        super(Iteration, self).__init__()
        self.element = element
        self.counter0 = counter0
        self.counter1 = counter1
        self.first = first
        self.last_counter0 = last_counter0
        self.last_counter1 = self.total = None if self.last_counter0 is None else self.last_counter0 + 1

    def __iter__(self):
        return iter((self, self.element))

    @property
    def last(self):
        if self.last_counter0 is None:
            raise NotImplementedError("Iterator does not support getting size")
        return self.counter0 == self.last_counter0


def iter_cartesian_dicts(d):
    """Given a dictionary of the form {name: values}, yields dictionaries corresponding to the cartesian
    product of the values, assigned to their respective names"""
    keys = list(d)  # save keys order to prevent dictionary order changes
    for combination in itertools.product(*itervalues(d)):
        yield dict(zip(keys, combination))
