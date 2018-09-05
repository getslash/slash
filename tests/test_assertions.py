from .utils import (
    CustomException,
)
from contextlib import contextmanager

import pytest

import slash
from slash import should
from slash.exceptions import TestFailed as _TestFailed, ExpectedExceptionNotCaught


@pytest.mark.parametrize('pair', [
    (1, 1),
    (1, 1.00000001),
])
@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_assert_almost_equal_positive(pair):
    a, b = pair
    slash.assert_almost_equal(a, b)


@pytest.mark.parametrize('combination', [
    (1, 1, 0),
    (1, 1, 0.1),
    (1, 1.1, 0.5),
    (1.0001, 1.00009, 0.00002),
])
@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_assert_almost_equal_positive_with_delta(combination):
    a, b, delta = combination
    slash.assert_almost_equal(a, b, delta)


@pytest.mark.parametrize('combination', [
    (1, 12, 0),
    (1, 1.1, 0.00001),
    (1.0001, 1.00009, 0.000001),
])
@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_assert_almost_equal_negative_with_delta(combination):
    a, b, delta = combination
    with pytest.raises(AssertionError):
        slash.assert_almost_equal(a, b, delta)


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_assert_equals():
    with checking(should.equal, should.not_equal):
        good(1, 1)
        bad(1, 2)


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_assert_empty():
    with checking(should.be_empty, should.not_be_empty):
        good([])
        good({})
        good(set())
        bad([1, 2, 3])
        bad({1: 2})
        bad(set([1, 2, 3]))


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_assert_isinstance():
    with checking(should.be_a, should.not_be_a):
        good(1, int)
        good("a", str)
        good({}, dict)
        bad(1, 1)
        bad(1, str)
        bad(None, str)


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_is_none():
    with checking(should.be_none, should.not_be_none):
        good(None)
        bad("None")


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_is():
    obj = object()
    with checking(should.be, should.not_be):
        good(obj, obj)
        bad(obj, object())
        bad({}, {})


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_truth():
    with checking(should.be_true, should.be_false):
        good(True)
        good("hello")
        bad(False)
        bad("")
        bad({})


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_in():
    with checking(should.be_in, should.not_be_in):
        good(1, [1, 2, 3])
        good("e", "hello")
        bad(1, [])
        bad("e", "fdfd")
    with checking(should.contain, should.not_contain):
        good([1, 2, 3], 1)
        good("hello", "e")
        bad("fdfdfd", "e")



@pytest.mark.usefixtures('disable_vintage_deprecations')
@pytest.mark.parametrize('func', [should.raise_exception, slash.assert_raises])
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
        assert False, "should.raise_exception allowed success"


@pytest.mark.usefixtures('disable_vintage_deprecations')
@pytest.mark.parametrize('func', [should.raise_exception, slash.assert_raises])
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




@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_raises_exception_multiple_classes():
    possible_exception_types = (CustomException, OtherException)
    for x in possible_exception_types:
        with should.raise_exception(possible_exception_types):
            raise x()

    with pytest.raises(ExpectedExceptionNotCaught):
        with should.raise_exception((CustomException,)):
            pass

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
