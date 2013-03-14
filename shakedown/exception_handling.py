from contextlib import contextmanager
import sys

_EXCEPTION_HANDLERS = [
    ]

@contextmanager
def handling_exceptions():
    try:
        yield
    except:
        handle_exception(sys.exc_info())
        raise

def handle_exception(exc_info):
    if not is_exception_handled(exc_info[1]):
        for handler in _EXCEPTION_HANDLERS:
            handler(exc_info)
    mark_exception_handled(exc_info[1])

def mark_exception_handled(e):
    mark_exception(e, "handled", True)

def is_exception_handled(e):
    """
    Checks if the exception ``e`` already passed through the exception handling logic
    """
    return bool(get_exception_mark(e, "handled", False))

_NO_DEFAULT = object()

def is_exception_marked(e, name):
    return get_exception_mark(e, name, _NO_DEFAULT) is not _NO_DEFAULT

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
    returned = getattr(e, "__shakedown_exc_marks__", None)
    if returned is None:
        returned = e.__shakedown_exc_marks__ = {}
    return returned
