from slash.frontend.slash_fixtures import slash_fixtures
from slash._compat import StringIO


def test_fixture_cleanup_at_end_of_suite(suite):
    suite.debug_info = False
    f = suite.slashconf.add_fixture()
    path = suite.commit()
    report_stream = StringIO()

    slash_fixtures([path], report_stream)
    assert 'Source' in report_stream.getvalue()
