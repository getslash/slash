from slash.frontend.slash_fixtures import slash_fixtures
from slash._compat import StringIO


def test_fixture_cleanup_at_end_of_suite(populated_suite):
    populated_suite.add_fixture()
    path = populated_suite.commit()
    report_stream = StringIO()

    slash_fixtures([path], report_stream)
    assert 'Source' in report_stream.getvalue()
