from slash.frontend.list_config import list_config
from slash._compat import StringIO


def test_slash_list():
    report_stream = StringIO()
    list_config([], report_stream)
    assert report_stream.getvalue()


