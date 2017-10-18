import operator
import sys

import logbook
from vintage import deprecated

from . import exception_handling
from ._compat import PY2
from .exceptions import TestFailed, ExpectedExceptionNotCaught
from .utils import operator_information

sys.modules["slash.should"] = sys.modules[__name__]
_logger = logbook.Logger(__name__)

def _deprecated(func, message=None):
    return deprecated(since='0.19.0', what='slash.should.{0.__name__}'.format(func),
                      message=message or 'Use plain assertions instead')(func)


def _binary_assertion(name, operator_func):
    op = operator_information.get_operator_by_func(operator_func)

    def _assertion(a, b, msg=None):
        if not op(a, b):
            msg = _get_message(msg, operator_information.get_operator_by_func(
                op.inverse_func).to_expression(a, b))
            raise TestFailed(msg)
    _assertion.__name__ = name
    _assertion.__doc__ = "Asserts **{0}**".format(
        op.to_expression("ARG1", "ARG2"))
    _assertion = _deprecated(_assertion)
    return _assertion


def _unary_assertion(name, operator_func):
    op = operator_information.get_operator_by_func(operator_func)

    def _assertion(a, msg=None):
        if not op(a):
            msg = _get_message(msg, operator_information.get_operator_by_func(
                op.inverse_func).to_expression(a))
            raise TestFailed(msg)
    _assertion.__name__ = name
    _assertion.__doc__ = "Asserts **{0}**".format(op.to_expression("ARG"))
    _assertion = _deprecated(_assertion)
    return _assertion


def _get_message(msg, description):
    if msg is None:
        return description
    return "{0} ({1})".format(msg, description)

equal = _binary_assertion("equal", operator.eq)
assert_equal = assert_equals = equal = equal

not_equal = _binary_assertion("not_equal", operator.ne)
assert_not_equal = assert_not_equals = not_equals = not_equal

be_a = _binary_assertion("be_a", operator_information.safe_isinstance)
assert_isinstance = be_a

not_be_a = _binary_assertion(
    "not_be_a", operator_information.safe_not_isinstance)
assert_not_isinstance = not_be_a

be_none = _unary_assertion("be_none", operator_information.is_none)
assert_is_none = be_none

not_be_none = _unary_assertion("not_be_none", operator_information.is_not_none)
assert_is_not_none = not_be_none

be = _binary_assertion("be", operator.is_)
assert_is = be

not_be = _binary_assertion("not_be", operator.is_not)
assert_is_not = not_be

be_true = _unary_assertion("be_true", operator.truth)
assert_true = be_true

be_false = _unary_assertion("be_false", operator.not_)
assert_false = be_false

be_empty = _unary_assertion("be_empty", operator_information.is_empty)
assert_empty = assert_is_empty = be_empty

not_be_empty = _unary_assertion(
    "not_be_empty", operator_information.is_not_empty)
assert_not_empty = assert_is_not_empty = not_be_empty

contain = _binary_assertion("contain", operator.contains)
assert_contains = contains = contain

not_contain = _binary_assertion(
    "not_contain", operator_information.not_contains)
assert_not_contains = assert_not_contain = not_contains = not_contain


def be_in(a, b, msg=None):
    """
    Asserts **ARG1 in ARG2**
    """
    return contain(b, a, msg)
assert_in = be_in


def not_be_in(a, b, msg=None):
    """
    Asserts **ARG1 not in ARG2**
    """
    return not_contain(b, a, msg)
assert_not_in = not_be_in


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
                if PY2:
                    sys.exc_clear()  # pylint: disable=no-member
                return True
            return None
        msg = self._msg
        if self._msg is None:
            expected_classes = self._expected_classes
            if not isinstance(expected_classes, tuple):
                expected_classes = (expected_classes, )
            msg = "{0} not raised".format("/".join(e.__name__ for e in expected_classes))
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


@deprecated(since='0.19.0', what='slash.should.raise_exception', message='Use slash.assert_raises instead')
def raise_exception(exception_class, msg=None):
    return assert_raises(exception_class, msg=msg)

raise_exception.__doc__ = assert_raises.__doc__.replace("assert_raises", "raise_exception")


def assert_almost_equal(a, b, delta=0.00000001):
    """Asserts that abs(a - b) <= delta
    """
    assert abs(a - b) <= delta


class _CaughtException(object):
    exception = None
