import munch
from slash.frontend.list_config import list_config
from io import StringIO


def test_slash_list_config():
    report_stream = StringIO()
    list_config(munch.Munch(argv=[]), report_stream)
    assert report_stream.getvalue()

def test_slash_list_config_with_filters():
    report_stream = StringIO()
    list_config(munch.Munch(argv=['log']), report_stream)
    assert 'log.root' in report_stream.getvalue()
