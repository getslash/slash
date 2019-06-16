from .utils import (
    CustomException,
)
from contextlib import contextmanager

import pytest

import slash
from slash.exceptions import TestFailed as _TestFailed, ExpectedExceptionNotCaught


@pytest.mark.parametrize('pair', [
    (1, 1),
    (1, 1.00000001),
])
def test_assert_almost_equal_positive(pair):
    a, b = pair
    slash.assert_almost_equal(a, b)


@pytest.mark.parametrize('combination', [
    (1, 1, 0),
    (1, 1, 0.1),
    (1, 1.1, 0.5),
    (1.0001, 1.00009, 0.00002),
])
def test_assert_almost_equal_positive_with_delta(combination):
    a, b, delta = combination
    slash.assert_almost_equal(a, b, delta)


@pytest.mark.parametrize('combination', [
    (1, 12, 0),
    (1, 1.1, 0.00001),
    (1.0001, 1.00009, 0.000001),
])
def test_assert_almost_equal_negative_with_delta(combination):
    a, b, delta = combination
    with pytest.raises(AssertionError):
        slash.assert_almost_equal(a, b, delta)


@pytest.mark.parametrize('func', [slash.assert_raises])
def test_assert_raises(func):
    thrown = CustomException()
    with func(CustomException) as caught:
        raise thrown
    assert caught.exception is thrown
    try:
        with func(CustomException):
            raise OtherException()
    except OtherException:
        pass
    else:
        assert False, "func allowed a different type of exception to be raised"
    try:
        with func(CustomException):
            pass
    except ExpectedExceptionNotCaught as e:
        assert " not raised" in str(e)
        assert e.expected_types == (CustomException,)
    else:
        assert False, "assert_raises allowed success"


@pytest.mark.parametrize('func', [slash.assert_raises])
def test_assert_raises_multiple_exceptions(func):
    class CustomException1(Exception):
        pass

    class CustomException2(Exception):
        pass

    class CustomException3(Exception):
        pass

    exception_types = (CustomException1, CustomException2)

    for exc_type in exception_types:
        with func(exception_types) as caught:
            value = exc_type('!')
            raise value
        assert caught.exception is value

    value = CustomException3('!')
    with pytest.raises(CustomException3) as caught:
        with func(exception_types):
            raise value
    assert caught.value is value

# boilerplate


class OtherException(BaseException):
    pass

_MESSAGE = "SOME MESSAGE HERE"


def good(*args):
    _test_assertion(args, positive=True)


def bad(*args):
    _test_assertion(args, positive=False)


def _test_assertion(args, positive):
    positive_assertion = _current_positive_assertion
    negative_assertion = _current_negative_assertion
    if not positive:
        positive_assertion, negative_assertion = negative_assertion, positive_assertion
    positive_assertion(*args)
    positive_assertion(*(args + (_MESSAGE,)))
    for msg in (None, _MESSAGE):
        try:
            negative_assertion(*(args + (msg,)))
        except _TestFailed as e:
            if msg is not None:
                assert msg in str(e)
        else:
            assert False, "Assertion did not fail"


_current_positive_assertion = None
_current_negative_assertion = None


@contextmanager
def checking(assertion, negative_assertion):
    global _current_positive_assertion # pylint: disable=global-statement
    global _current_negative_assertion # pylint: disable=global-statement
    assert _current_positive_assertion is None
    _current_positive_assertion = assertion
    _current_negative_assertion = negative_assertion
    try:
        yield
    finally:
        _current_positive_assertion = None
        _current_negative_assertion = None
