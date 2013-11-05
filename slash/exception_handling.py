from contextlib import contextmanager
from .utils.debug import debug_if_needed
from . import hooks as trigger_hook
from .ctx import context as slash_context
from .conf import config
from .exceptions import TestFailed, SkipTest
import functools
import logbook
try:
    import raven # pylint: disable=F0401
except ImportError:
    raven = None
import sys

_logger = logbook.Logger(__name__)

def update_current_result(exc_info):
    if slash_context.session is None:
        return
    if slash_context.test is not None:
        current_result = slash_context.session.results.get_result(slash_context.test)
    else:
        current_result = slash_context.session.results.global_result

    exc_class = exc_info[0]
    if issubclass(exc_class, TestFailed):
        current_result.add_failure()
    elif issubclass(exc_class, Exception) and not issubclass(exc_class, SkipTest):
        current_result.add_error()

def trigger_hooks_before_debugger(_):
    trigger_hook.exception_caught_before_debugger()
def trigger_hooks_after_debugger(_):
    trigger_hook.exception_caught_after_debugger()

_EXCEPTION_HANDLERS = [
    update_current_result,
    trigger_hooks_before_debugger,
    debug_if_needed,
    trigger_hooks_after_debugger,
    ]

@contextmanager
def handling_exceptions(**kwargs):
    swallow = kwargs.pop("swallow", False)
    try:
        yield
    except:
        handle_exception(sys.exc_info(), **kwargs)
        if not swallow:
            raise

def handle_exception(exc_info, context=None):
    """
    Call any handlers or debugging code before propagating an exception onwards.

    This makes sure that the exception can be handled as close as possible to its originating point.

    .. note:: this *DOES NOT* take care of adding the error to the session or test results!
    """
    msg = "Handling exception"
    if context is not None:
        msg += " (Context: {0})"
    _logger.debug(msg, context, exc_info=exc_info)
    if not is_exception_handled(exc_info[1]):
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
    returned = getattr(e, "__slash_exc_marks__", None)
    if returned is None:
        returned = e.__slash_exc_marks__ = {}
    return returned

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
