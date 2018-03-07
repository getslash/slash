from contextlib import contextmanager
from .utils.debug import debug_if_needed
from .utils.exception_mark import mark_exception, get_exception_mark
from .utils.traceback_proxy import create_traceback_proxy
from . import hooks as trigger_hook
from . import exceptions
from ._compat import PY2, PYPY
from .ctx import context as slash_context
from .conf import config

import functools
import threading
import logbook
try:
    import raven  # pylint: disable=F0401
except ImportError:
    raven = None
import sys

_logger = logbook.Logger(__name__)
NO_EXC_INFO = (None, None, None)


def update_current_result(exc_info):  # pylint: disable=unused-argument
    if slash_context.session is None:
        return
    if slash_context.test is not None:
        current_result = slash_context.session.results.get_result(slash_context.test)
    else:
        current_result = slash_context.session.results.global_result

    current_result.add_exception(exc_info)


def trigger_hooks_before_debugger(_):
    trigger_hook.exception_caught_before_debugger()  # pylint: disable=no-member


def trigger_hooks_after_debugger(_):
    trigger_hook.exception_caught_after_debugger()  # pylint: disable=no-member


_EXCEPTION_HANDLERS = [
    update_current_result,
    trigger_hooks_before_debugger,
    debug_if_needed,
    trigger_hooks_after_debugger,
]


class _IgnoredState(threading.local):
    ignored_exception_types = ()

_ignored_state = _IgnoredState()


class thread_ignore_exception_context(object):

    def __init__(self, exc_type):
        super(thread_ignore_exception_context, self).__init__()
        self._exc_type = exc_type
        self._prev = None

    def __enter__(self):
        self._prev = _ignored_state.ignored_exception_types
        _ignored_state.ignored_exception_types = list(_ignored_state.ignored_exception_types) + [self._exc_type]

    def __exit__(self, *_):
        _ignored_state.ignored_exception_types = self._prev
        self._prev = None


def handling_exceptions(fake_traceback=True, **kwargs):
    """Context manager handling exceptions that are raised within it

    :param passthrough_types: a tuple specifying exception types to avoid handling, raising them immediately onward
    :param swallow: causes this context to swallow exceptions
    :param swallow_types: causes the context to swallow exceptions of, or derived from, the specified types
    :param context: An optional string describing the operation being wrapped. This will be emitted to the logs to simplify readability

    .. note:: certain exceptions are never swallowed - most notably KeyboardInterrupt, SystemExit, and SkipTest
    """

    if not PYPY and fake_traceback:
        # Only in CPython we're able to fake the original, full traceback
        try:
            fake_tbs = create_traceback_proxy(frame_correction=2)
        except (KeyError, IndexError):
            _logger.warn("Could not extract full traceback for exceptions handling")
            fake_tbs = tuple()
    else:
        fake_tbs = tuple()
    swallow = kwargs.pop("swallow", False)
    swallow_types = kwargs.pop('swallow_types', ())
    if swallow:
        swallow_types = swallow_types + (Exception, )
    assert isinstance(swallow_types, (list, tuple)), 'swallow_types must be either a list or a tuple'
    passthrough_types = kwargs.pop('passthrough_types', ()) + tuple(_ignored_state.ignored_exception_types)
    return _HandlingException(fake_tbs, swallow_types, passthrough_types, kwargs)


class _HandledException(object):
    exception = None

class _HandlingException(object):

    def __init__(self, fake_tbs, swallow_types, passthrough_types, handling_kwargs):
        self._fake_traceback = fake_tbs
        self._kwargs = handling_kwargs
        self._passthrough_types = passthrough_types
        self._swallow_types = swallow_types
        self._handled = _HandledException()

    def __enter__(self):
        return self._handled

    def __exit__(self, *exc_info):
        if not exc_info or exc_info == NO_EXC_INFO:
            return
        exc_value = exc_info[1]

        if isinstance(exc_value, self._passthrough_types):
            return None

        if self._fake_traceback:
            (first_tb, last_tb) = self._fake_traceback
            (second_tb, _) = create_traceback_proxy(exc_info[2])
            last_tb.tb_next = second_tb
            exc_info = (exc_info[0], exc_info[1], first_tb._tb) # pylint: disable=protected-access
        handle_exception(exc_info, **self._kwargs)
        self._handled.exception = exc_info[1]
        skip_types = () if slash_context.session is None else slash_context.session.get_skip_exception_types()
        if isinstance(exc_value, skip_types) or isinstance(exc_value, exceptions.INTERRUPTION_EXCEPTIONS):
            return None
        if self._swallow_types and isinstance(exc_value, self._swallow_types):
            if PY2:
                sys.exc_clear()  # pylint: disable=no-member
            _logger.trace('Swallowing {!r}', exc_value)
            return True
        return None


def handle_exception(exc_info, context=None):
    """
    Call any handlers or debugging code before propagating an exception onwards.

    This makes sure that the exception can be handled as close as possible to its originating point.

    It also adds the exception to its correct place in the current result, be it a failure, an error or a skip

    """
    already_handled = is_exception_handled(exc_info[1])
    msg = "Handling exception"
    if context is not None:
        msg += " (Context: {0})"
    if already_handled:
        msg += " (already handled)"
    _logger.debug(msg, context, exc_info=exc_info if not already_handled else None)

    if not already_handled:
        mark_exception_handled(exc_info[1])
        for handler in _EXCEPTION_HANDLERS:
            handler(exc_info)


def mark_exception_handled(e):
    return mark_exception(e, "handled", True)


def is_exception_handled(e):
    """
    Checks if the exception ``e`` already passed through the exception handling logic
    """
    return bool(get_exception_mark(e, "handled", False))


@contextmanager
def get_exception_swallowing_context(report_to_sentry=True):
    """
    Returns a context under which all exceptions are swallowed (ignored)
    """
    try:
        yield
    except:
        if not get_exception_mark(sys.exc_info()[1], "swallow", True):
            raise
        if report_to_sentry:
            capture_sentry_exception()
        _logger.debug("Ignoring exception", exc_info=sys.exc_info())


def noswallow(exception):
    """
    Marks an exception to prevent swallowing by :func:`slash.exception_handling.get_exception_swallowing_context`,
    and returns it
    """
    mark_exception(exception, "swallow", False)
    return exception


def mark_exception_fatal(exception):
    """
    Causes this exception to halt the execution of the entire run.

    This is useful when detecting errors that need careful examination, thus preventing further tests from
    altering the test subject's state
    """
    mark_exception(exception, "fatal", True)
    return exception


def mark_exception_frame_correction(exception, correction=+1):
    current_correction = get_exception_frame_correction(exception)
    return mark_exception(exception, 'frame_correction', current_correction + correction)


def get_exception_frame_correction(exception):
    return get_exception_mark(exception, 'frame_correction', 0)


def is_exception_fatal(exception):
    return bool(get_exception_mark(exception, "fatal", False))


def inhibit_unhandled_exception_traceback(exception):
    """
    Causes this exception to inhibit console tracback
    """
    mark_exception(exception, "inhibit_console_tb", True)
    return exception


def should_inhibit_unhandled_exception_traceback(exception):
    return bool(get_exception_mark(exception, "inhibit_console_tb", False))


def disable_exception_swallowing(func_or_exception):
    """
    Marks an exception to prevent swallowing. Can also be used as a decorator around a function to mark all escaped
    exceptions
    """
    if isinstance(func_or_exception, BaseException):
        return noswallow(func_or_exception)

    @functools.wraps(func_or_exception)
    def func(*args, **kwargs):
        try:
            return func_or_exception(*args, **kwargs)
        except BaseException as e:
            disable_exception_swallowing(e)
            raise
    return func


def capture_sentry_exception():
    client = get_sentry_client()
    if client is not None:
        client.captureException()


def get_sentry_client():
    if raven is not None and config.root.sentry.dsn:
        return raven.Client(config.root.sentry.dsn)
    return None
