from slash.utils.exception_mark import ExceptionMarker

def test_marker():
    exc = AttributeError()
    marker = ExceptionMarker('mark')
    assert not marker.is_exception_marked(exc)
    marker.mark_exception(exc)
    assert marker.is_exception_marked(exc)

