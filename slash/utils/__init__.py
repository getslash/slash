import functools
import sys

import logbook

from .._compat import string_types
from ..ctx import context
from ..exceptions import SkipTest
from ..runnable_test_factory import RunnableTestFactory


def skip_test(*args):
    """
    Skips the current test execution by raising a :class:`slash.exceptions.SkipTest`
    exception. It can optionally receive a reason argument.
    """
    raise SkipTest(*args)


def skipped(thing, reason=None):
    """
    A decorator for skipping methods and classes
    """
    if isinstance(thing, str):
        return functools.partial(skipped, reason=thing)
    if isinstance(thing, type) and issubclass(thing, RunnableTestFactory):
        thing.skip_all(reason)
        return thing

    @functools.wraps(thing)
    def new_func(*_, **__):  # pylint: disable=unused-argument
        skip_test(reason)
    return new_func


def add_error(msg):
    """
    Adds an error to the current test result

    :param msg: can be either an object or a string representing a message
    """
    if context.session is not None:
        context.session.results.current.add_error(msg)


def add_failure(msg):
    """
    Adds a failure to the current test result

    :param msg: can be either an object or a string representing a message
    """
    if context.session is not None:
        context.session.results.current.add_failure(msg)

_deprecation_logger = logbook.Logger("slash.deprecation")
_deprecation_locations = set()

def deprecated(func=None, message=None):
    """Marks the specified function as deprecated, and emits a warning when it's called
    """
    if isinstance(func, string_types):
        assert message is None
        message = func
        func = None

    if func is None:
        return functools.partial(deprecated, message=message)

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        caller_location = _get_caller_location()
        if caller_location not in _deprecation_locations:
            warning = "{func.__module__}.{func.__name__} is deprecated.".format(func=func)
            if message is not None:
                warning += " {0}".format(message)
            _deprecation_logger.warning(warning)
            _deprecation_locations.add(caller_location)
        return func(*args, **kwargs)

    if new_func.__doc__:  # pylint: disable=no-member
        new_func.__doc__ += "\n.. deprecated::\n"  # pylint: disable=no-member
        if message:
            new_func.__doc__ += "   {0}".format(message)  # pylint: disable=no-member

    return new_func

def _get_caller_location(stack_climb=2):
    frame = sys._getframe(stack_climb)  # pylint: disable=protected-access
    try:
        return (frame.f_code.co_name, frame.f_lineno)
    finally:
        del frame
