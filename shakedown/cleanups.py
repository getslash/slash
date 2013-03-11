from collections import deque
from .ctx import context

def add_cleanup(_func, *args, **kwargs):
    _get_cleanups().append((_func, args, kwargs))

def call_cleanups():
    cleanups = _get_cleanups()
    while cleanups:
        func, args, kwargs = cleanups.popleft()
        try:
            func(*args, **kwargs) # pylint: disable=W0142
        except:
            context.suite.get_result(context.test).add_error()

def _get_cleanups():
    returned = getattr(context, "cleanups", None)
    if returned is None:
        returned = context.cleanups = deque()
    return returned
