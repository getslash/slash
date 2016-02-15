from slash.utils.exception_mark import ExceptionMarker, mark_exception, get_exception_mark

def test_marker():
    exc = AttributeError()
    marker = ExceptionMarker('mark')
    assert not marker.is_exception_marked(exc)
    marker.mark_exception(exc)
    assert marker.is_exception_marked(exc)


def test_marker_mark_returns_exception():
    exc = AttributeError()
    assert ExceptionMarker('mark').mark_exception(exc) is exc
    assert ExceptionMarker('mark').is_exception_marked(exc)

def test_marker_class():

    class CustomException(Exception):
        pass
    mark_exception(CustomException, 'a', 'b')
    assert get_exception_mark(CustomException, 'a') == 'b'

    e = CustomException()
    mark_exception(e, 'c', 'd')
    assert get_exception_mark(e, 'a') == 'b'
    assert get_exception_mark(e, 'c') == 'd'
    assert get_exception_mark(CustomException, 'c') is None
