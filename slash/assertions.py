import logbook

from . import exception_handling
from .exceptions import ExpectedExceptionNotCaught

_logger = logbook.Logger(__name__)


def _get_message(msg, description):
    if msg is None:
        return description
    return "{} ({})".format(msg, description)


class _CaughtContext(object):

    def __init__(self, message, exc_types, ensure_caught):
        if not isinstance(exc_types, tuple):
            exc_types = (exc_types, )
        self._expected_classes = exc_types
        self._caught = _CaughtException()
        self._ignore_ctx = None
        self._msg = message
        self._ensure_caught = ensure_caught

    def __enter__(self):
        self._ignore_ctx = exception_handling.thread_ignore_exception_context(self._expected_classes)
        self._ignore_ctx.__enter__()  # pylint: disable=no-member
        return self._caught

    def __exit__(self, *exc_info):
        if self._ignore_ctx:
            self._ignore_ctx.__exit__(*exc_info)  # pylint: disable=no-member
        if exc_info and exc_info != exception_handling.NO_EXC_INFO:
            e = exc_info[1]
            if isinstance(e, self._expected_classes):
                self._caught.exception = e
                return True
            return None
        msg = self._msg
        if self._msg is None:
            expected_classes = self._expected_classes
            if not isinstance(expected_classes, tuple):
                expected_classes = (expected_classes, )
            msg = "{} not raised".format("/".join(e.__name__ for e in expected_classes))
        if self._ensure_caught:
            raise ExpectedExceptionNotCaught(msg, self._expected_classes)
        _logger.debug(msg)
        return True


def assert_raises(exception_class, msg=None):
    """
    Ensures a subclass of **ARG1** leaves the wrapped context:

    >>> with assert_raises(AttributeError):
    ...     raise AttributeError()
    """
    return _CaughtContext(msg, exception_class, ensure_caught=True)


def allowing_exceptions(exception_class, msg=None):
    """
    Allow subclass of **ARG1** to be raised during context:

    >>> with allowing_exceptions(AttributeError):
    ...     raise AttributeError()
    >>> with allowing_exceptions(AttributeError):
    ...     pass
    """
    return _CaughtContext(msg, exception_class, ensure_caught=False)


def assert_almost_equal(a, b, delta=0.00000001):
    """Asserts that abs(a - b) <= delta
    """
    assert abs(a - b) <= delta


class _CaughtException(object):
    exception = None
