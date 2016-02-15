import copy


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

_EXCEPTION_MARKS_NAME = '__slash_exc_marks__'

def _ensure_exception_marks(e):
    returned = getattr(e, _EXCEPTION_MARKS_NAME, None)
    if returned is not None and not isinstance(e, type) and returned is getattr(type(e), _EXCEPTION_MARKS_NAME, None):
        returned = copy.deepcopy(returned)
        setattr(e, _EXCEPTION_MARKS_NAME, returned)
    if returned is None:
        returned = {}
        setattr(e, _EXCEPTION_MARKS_NAME, returned)
    return returned

class ExceptionMarker(object):

    def __init__(self, name):
        super(ExceptionMarker, self).__init__()
        self.name = name

    def mark_exception(self, e):
        mark_exception(e, self.name, True)
        return e

    def is_exception_marked(self, e):
        return bool(get_exception_mark(e, self.name, False))
