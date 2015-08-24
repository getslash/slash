import functools
import sys
import threading
from contextlib import contextmanager

import logbook

from .._compat import string_types

_deprecation_logger = logbook.Logger("slash.deprecation")
_deprecation_locations = set()

class _Local(threading.local):
    enabled = True

_local = _Local()


@contextmanager
def get_no_deprecations_context():
    """Disables deprecation messages temporarily
    """
    prev_enabled = _local.enabled
    _local.enabled = False
    try:
        yield
    finally:
        _local.enabled = prev_enabled


def deprecated(func=None, message=None, since=None, what=None, frame_correction=0):
    """Marks the specified function as deprecated, and emits a warning when it's called
    """
    if isinstance(func, string_types):
        assert message is None
        message = func
        func = None

    if func is None:
        return functools.partial(
            deprecated,
            message=message, since=since, what=what,
            frame_correction=frame_correction)

    if not since:
        raise ValueError(
            "Must provide deprecation version via the 'since' parameter")

    if what is None:
        what = '{func.__module__}.{func.__name__}'.format(func=func)

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        if _local.enabled:
            caller_location = _get_caller_location()
            if caller_location not in _deprecation_locations:
                warning = "{what} is deprecated.".format(
                    what=what)
                if message is not None:
                    warning += " {0}".format(message)
                _deprecation_logger.warning(warning, frame_correction=frame_correction+1)
                _deprecation_locations.add(caller_location)
        return func(*args, **kwargs)

    if new_func.__doc__:  # pylint: disable=no-member
        new_func.__doc__ += "\n.. deprecated:: {0}\n".format(since)  # pylint: disable=no-member
        if message:
            new_func.__doc__ += "   {0}".format(message)  # pylint: disable=no-member

    return new_func


def _get_caller_location(stack_climb=2):
    frame = sys._getframe(stack_climb)  # pylint: disable=protected-access
    try:
        return (frame.f_code.co_name, frame.f_lineno)
    finally:
        del frame
