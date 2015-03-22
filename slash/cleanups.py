from .ctx import context
from .exception_handling import handling_exceptions
import logbook

_logger = logbook.Logger(__name__)


class _Cleanup(object):

    def __init__(self, func, args, kwargs, critical=False, success_only=False):
        assert not (success_only and critical)
        super(_Cleanup, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.critical = critical
        self.success_only = success_only

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    def __repr__(self):
        return "{0} ({1},{2})".format(self.func, self.args, self.kwargs)


def add_cleanup(_func, *args, **kwargs):
    """
    Adds a cleanup function to the cleanup stack. Cleanups are executed in a LIFO order.

    Positional arguments and keywords are passed to the cleanup function when called.

    :param critical: If True, this cleanup will take place even when tests are interrupted by the user (Using Ctrl+C for instance)
    :param success_only: If True, execute this cleanup only if no errors are encountered
    :param args: positional arguments to pass to the cleanup function
    :param kwargs: keyword arguments to pass to the cleanup function
    """
    critical = kwargs.pop('critical', False)
    success_only = kwargs.pop('success_only', False)

    new_kwargs = kwargs.pop('kwargs', {}).copy()
    new_args = list(kwargs.pop('args', ()))
    if args or kwargs:
        _logger.warning(
            'Passing *args/**kwargs to slash.add_cleanup is deprecated')
        new_args.extend(args)
        new_kwargs.update(kwargs)

    added = _Cleanup(_func, new_args, new_kwargs, critical=critical, success_only=success_only)
    _get_cleanups().append(added)


def add_critical_cleanup(_func, *args, **kwargs):
    """
    Same as :func:`.add_cleanup`, only the cleanup will be called even on interrupted tests
    """
    return add_cleanup(_func, critical=True, *args, **kwargs)


def add_success_only_cleanup(_func, *args, **kwargs):
    """
    Same as :func:`.add_cleanup`, only the cleanup will be called only if the test succeeds
    """
    return add_cleanup(_func, success_only=True, *args, **kwargs)


def call_cleanups(critical_only=False, success_only=False):
    cleanups = _get_cleanups()
    while cleanups:
        cleanup = cleanups.pop()
        if critical_only and not cleanup.critical:
            continue
        if not success_only and cleanup.success_only:
            continue
        with handling_exceptions(swallow=True):
            _logger.debug("Calling cleanup: {0}", cleanup)
            cleanup()


def _get_cleanups():
    returned = getattr(context, "cleanups", None)
    if returned is None:
        returned = context.cleanups = []
    return returned
