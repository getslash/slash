class Details(object):

    def __init__(self, set_callback=None):
        super(Details, self).__init__()
        self._details = {}
        self._set_callback = set_callback

    def set(self, key, value):
        """Sets a specific detail (by name) to a specific value
        """
        if self._set_callback is not None:
            self._set_callback(key, value)
        self._details[key] = value

    def append(self, key, value):
        """Appends a value to a list key, or creates it if needed
        """
        lst = self._details.setdefault(key, [])
        if not isinstance(lst, list):
            raise TypeError('Cannot append value to a {.__class__.__name__!r} value'.format(lst))
        lst.append(value)
        if self._set_callback is not None:
            self._set_callback(key, lst)

    def all(self):
        return self._details.copy()

    def __nonzero__(self):
        return bool(self._details)

    __bool__ = __nonzero__

    def __contains__(self, key):
        return key in self._details
