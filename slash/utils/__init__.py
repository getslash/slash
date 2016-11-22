import functools

from ..ctx import context
from ..core.markers import repeat_marker
from ..core import requirements
from ..exceptions import SkipTest


def skip_test(*args):
    """
    Skips the current test execution by raising a :class:`slash.exceptions.SkipTest`
    exception. It can optionally receive a reason argument.
    """
    raise SkipTest(*args)

def repeat(num_repetitions):
    """
    Marks a test to be repeated multiple times when run
    """
    return repeat_marker(num_repetitions)


def skipped(thing, reason=None):
    """
    A decorator for skipping methods and classes
    """
    if isinstance(thing, str):
        return functools.partial(skipped, reason=thing)

    return requirements.requires(requirements.Skip(reason))(thing)

def register_skip_exception(exception_type):
    """
    Registers a custom exception type to be recognized a test skip. This makes the exception
    behave just as if the test called ``skip_test``

    .. note:: this must be called within an active session
    """
    context.session.register_skip_exception(exception_type)


def add_error(msg=None, frame_correction=0, exc_info=None):
    """
    Adds an error to the current test result

    :param msg: can be either an object or a string representing a message
    :param frame_correction: when delegating add_error from another function, specifies
      the amount of frames to skip to reach the actual cause of the added error
    :param exc_info: (optional) - the exc_info tuple of the exception being recorded
    """
    if context.session is not None:
        return context.session.results.current.add_error(msg, frame_correction=frame_correction+1, exc_info=exc_info)


def add_failure(msg=None, frame_correction=0, exc_info=None):
    """
    Adds a failure to the current test result

    :param msg: can be either an object or a string representing a message
    :param frame_correction: when delegating add_failure from another function, specifies
      the amount of frames to skip to reach the actual cause of the added failure
    """
    if context.session is not None:
        return context.session.results.current.add_failure(msg, frame_correction=frame_correction+1, exc_info=exc_info)


def set_test_detail(key, value):
    """
    Store an object providing additional information about the current running test in a certain key.
    Each test has its own storage.

    :param key: a hashable object
    :param value: can be either an object or a string representing additional details
    """
    if context.session is not None:
        context.session.results.current.set_test_detail(key, value)
