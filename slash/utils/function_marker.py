def function_marker(name):
    return Marker(name)

class Marker(object):

    def __init__(self, name):
        super(Marker, self).__init__()
        self._name = name
        self._mark = '__marked_{0}__'.format(self._name)

    def __call__(self, func):
        setattr(self._normalize(func), self._mark, True)
        return func

    def is_marked(self, func):
        return bool(getattr(self._normalize(func), self._mark, False))

    @staticmethod
    def _normalize(func):
        if isinstance(func, (classmethod, staticmethod)):
            func = func.__func__
        return func
