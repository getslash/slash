from contextlib import contextmanager
from .utils.debug import debug_if_needed
from .utils.exception_mark import mark_exception, get_exception_mark
from . import hooks as trigger_hook
from .ctx import context as slash_context
from .conf import config
from .exceptions import SkipTest
import functools
import logbook
try:
    import raven # pylint: disable=F0401
except ImportError:
    raven = None
import sys

_logger = logbook.Logger(__name__)

def update_current_result(exc_info):  # pylint: disable=unused-argument
    if slash_context.session is None:
        return
    if slash_context.test is not None:
        current_result = slash_context.session.results.get_result(slash_context.test)
    else:
        current_result = slash_context.session.results.global_result

    current_result.add_exception()

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

@contextmanager
def handling_exceptions(**kwargs):
    """Context manager handling exceptions that are raised within it

    :param passthrough_types: a tuple specifying exception types to avoid handling, raising them immediately onward
    :param swallow: causes this context to swallow exceptions

    .. note:: certain exceptions are never swallowed - most notably KeyboardInterrupt, SystemExit, and SkipTest
    """
    swallow = kwargs.pop("swallow", False)
    passthrough_types = kwargs.pop('passthrough_types', ())
    try:
        yield
    except passthrough_types:
        raise
    except:
        exc_info = _, exc_value, _ = sys.exc_info()
        handle_exception(exc_info, **kwargs)
        if isinstance(exc_value, SkipTest):
            raise
        if not swallow or not isinstance(exc_value, Exception):
            raise

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
    mark_exception(e, "handled", True)

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

def is_exception_fatal(exception):
    return bool(get_exception_mark(exception, "fatal", False))

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
