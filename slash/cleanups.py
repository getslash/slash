from .ctx import context
from .exception_handling import handling_exceptions
import logbook

_logger = logbook.Logger(__name__)

class _Cleanup(object):
    def __init__(self, func, args, kwargs, critical=False):
        super(_Cleanup, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.critical = critical
    def __call__(self):
        return self.func(*self.args, **self.kwargs) # pylint: disable=W0142

def add_cleanup(_func, *args, **kwargs):
    """
    Adds a cleanup function to the cleanup stack. Cleanups are executed in a LIFO order.

    Positional arguments and keywords are passed to the cleanup function when called.
    """
    _add_cleanup(_Cleanup(_func, args, kwargs))

def add_critical_cleanup(_func, *args, **kwargs):
    """
    Same as :func:`.add_cleanup`, only the cleanup will be called even on interrupted tests
    """
    _add_cleanup(_Cleanup(_func, args, kwargs, critical=True))

def _add_cleanup(cleanup):
    _get_cleanups().append(cleanup)

def call_cleanups(critical_only=False):
    cleanups = _get_cleanups()
    while cleanups:
        cleanup = cleanups.pop()
        if critical_only and not cleanup.critical:
            continue
        with handling_exceptions(swallow=True):
            cleanup()

def _get_cleanups():
    returned = getattr(context, "cleanups", None)
    if returned is None:
        returned = context.cleanups = []
    return returned
