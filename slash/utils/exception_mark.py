def mark_exception(e, name, value):
    """
    Associates a mark with a given value to the exception ``e``
    """
    _ensure_exception_marks(e)[name] = value


def get_exception_mark(e, name, default=None):
    """
    Given an exception and a label name, get the value associated with that mark label.
    If the label does not exist on the specified exception, ``default`` is returned.
    """
    return _ensure_exception_marks(e).get(name, default)


def _ensure_exception_marks(e):
    returned = getattr(e, "__slash_exc_marks__", None)
    if returned is None:
        returned = e.__slash_exc_marks__ = {}
    return returned

class ExceptionMarker(object):

    def __init__(self, name):
        super(ExceptionMarker, self).__init__()
        self.name = name

    def mark_exception(self, e):
        mark_exception(e, self.name, True)

    def is_exception_marked(self, e):
        return bool(get_exception_mark(e, self.name, False))
