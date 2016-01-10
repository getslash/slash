from slash.frontend.slash_list import slash_list
from slash._compat import StringIO

import pytest

@pytest.mark.parametrize('flag', ["--only-fixtures", "--only-tests", None])
def test_slash_list(suite, flag):
    suite.debug_info = False
    f = suite.slashconf.add_fixture()
    path = suite.commit()
    report_stream = StringIO()

    args = [path]
    if flag is not None:
        args.append(flag)
    slash_list(args, report_stream)
    assert report_stream.getvalue()


@pytest.mark.parametrize('should_show_tags', [True, False])
def test_slash_list_tests(suite, should_show_tags, suite_test):
    suite_test.add_decorator('slash.tag("bla")')
    suite.debug_info = False
    path = suite.commit()
    report_stream = StringIO()
    args = [path, '--only-tests']
    if should_show_tags:
        args.append('--show-tags')
    slash_list(args, report_stream)
    output = report_stream.getvalue()
    assert ('Tags' in output) == (should_show_tags)
