from sentinels import NOTHING

from .._compat import get_underlying_classmethod_function


def function_marker(name):
    return Marker(name)

class Marker(object):

    def __init__(self, name, value=True):
        super(Marker, self).__init__()
        self._name = name
        self._value = value
        self._mark = '__marked_{0}__'.format(self._name)

    def __call__(self, func):
        if not hasattr(func, '__call__') and not isinstance(func, (classmethod, staticmethod)):
            return Marker(self._name, func)

        setattr(self._normalize(func), self._mark, self._value)
        return func

    def is_marked(self, func):
        return hasattr(self._normalize(func), self._mark)

    def get_value(self, func, default=NOTHING):
        returned = getattr(self._normalize(func), self._mark, default)
        if returned is NOTHING:
            raise LookupError()
        return returned

    @staticmethod
    def _normalize(func):
        if isinstance(func, (classmethod, staticmethod)):
            return get_underlying_classmethod_function(func)
        return func
