from collections import deque
from .ctx import context

def add_cleanup(_func, *args, **kwargs):
    """
    Adds a cleanup function to the cleanup stack. Cleanups are executed in a LIFO order.

    Positional arguments and keywords are passed to the cleanup function when called.
    """
    _get_cleanups().append((_func, args, kwargs))

def call_cleanups():
    cleanups = _get_cleanups()
    while cleanups:
        func, args, kwargs = cleanups.popleft()
        try:
            func(*args, **kwargs) # pylint: disable=W0142
        except:
            context.session.get_result(context.test).add_error()

def _get_cleanups():
    returned = getattr(context, "cleanups", None)
    if returned is None:
        returned = context.cleanups = deque()
    return returned
