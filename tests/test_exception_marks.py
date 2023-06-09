import pytest
from slash.utils.exception_mark import ExceptionMarker, mark_exception, get_exception_mark


def test_marker(exception_class):
    exc = exception_class()
    marker = ExceptionMarker('mark')
    assert not marker.is_exception_marked(exc)
    marker.mark_exception(exc)
    assert marker.is_exception_marked(exc)


def test_marker_mark_returns_exception(exception_class):
    exc = exception_class()
    assert ExceptionMarker('mark').mark_exception(exc) is exc
    assert ExceptionMarker('mark').is_exception_marked(exc)


def test_marker_class(exception_class):
    mark_exception(exception_class, 'a', 'b')
    # Builtin types cannot be marked (on the class) either by setattr or by setting its __dict__:
    # >>> setattr(AttributeError, 'a', 'b')
    # TypeError: can't set attributes of built-in/extension type 'AttributeError'
    # >>> AttributeError.__dict__['a'] = 'b'
    # TypeError: 'mappingproxy' object does not support item assignment
    is_builtin_type = exception_class is AttributeError
    expected = None if is_builtin_type else 'b'
    assert get_exception_mark(exception_class, 'a') == expected

    e = exception_class()
    mark_exception(e, 'c', 'd')
    assert get_exception_mark(e, 'a') == expected
    assert get_exception_mark(e, 'c') == 'd'
    assert get_exception_mark(exception_class, 'c') is None


class CustomException1(Exception):
    pass


class CustomException2(Exception):
    def __setattr__(self, name, value):
        raise Exception('Set-attr name={} value={}'.format(name, value))  # pylint: disable=broad-exception-raised


@pytest.fixture(params=[CustomException1, CustomException2, AttributeError], name="exception_class")
def exception_class_fx(request):
    return request.param
