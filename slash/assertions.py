from .exceptions import TestFailed
from .utils import operator_information
from contextlib import contextmanager
import operator
import sys

sys.modules["slash.should"] = sys.modules[__name__]


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


@contextmanager
def raise_exception(exception_class, msg=None):
    """
    Ensures a subclass of **ARG1** leaves the wrapped context:

    >>> with raise_exception(AttributeError):
    ...     raise AttributeError()
    """
    caught = _CaughtException()
    try:
        yield caught
    except exception_class as e:
        caught.exception = e
    else:
        expected_classes = exception_class
        if msg is None:
            if not isinstance(expected_classes, tuple):
                expected_classes = (expected_classes,)
            msg = "{0} not raised".format("/".join(e.__name__ for e in expected_classes))
        raise TestFailed(msg)


def assert_raises(exception_class, msg=None):
    return raise_exception(exception_class, msg=msg)
assert_raises.__doc__ = raise_exception.__doc__.replace(
    "raise_exception", "assert_raises")


def assert_almost_equal(a, b, delta=0.00000001):
    """Asserts that abs(a - b) <= delta
    """
    assert abs(a - b) <= delta


class _CaughtException(object):
    exception = None

# def assertDictEqual(self, d1, d2, msg=None):
# def assertDictContainsSubset(self, expected, actual, msg=None):
# def assertItemsEqual(self, expected_seq, actual_seq, msg=None):
# def assertMultiLineEqual(self, first, second, msg=None):
# def assertLess(self, a, b, msg=None):
# def assertLessEqual(self, a, b, msg=None):
# def assertGreater(self, a, b, msg=None):
# def assertGreaterEqual(self, a, b, msg=None):
# def assertRaisesRegexp(self, expected_exception, expected_regexp,
# def assertRegexpMatches(self, text, expected_regexp, msg=None):
# def assertNotRegexpMatches(self, text, unexpected_regexp, msg=None):
# def assertSequenceEqual(self, seq1, seq2, msg=None, seq_type=None):
# def assertAlmostEqual(self, first, second, places=None, msg=None, delta=None):
# def assertNotAlmostEqual(self, first, second, places=None, msg=None, delta=None):
#
