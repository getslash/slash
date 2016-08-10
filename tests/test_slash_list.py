import os
import re
from slash.frontend.slash_list import slash_list
from slash._compat import StringIO
from .utils.suite_writer import Suite

import pytest


@pytest.mark.parametrize('flag', ["--only-fixtures", "--only-tests", None])
def test_slash_list(suite, flag):
    suite.debug_info = False
    _ = suite.slashconf.add_fixture()
    path = suite.commit()
    report_stream = StringIO()

    args = [path]
    if flag is not None:
        args.append(flag)
    slash_list(args, report_stream)
    assert report_stream.getvalue()


@pytest.mark.parametrize('allow_empty', [True, False])
def test_slash_list_without_any_tests(allow_empty):
    empty_suite = Suite()
    empty_suite.debug_info = False
    path = empty_suite.commit()
    report_stream = StringIO()
    args = [path]
    if allow_empty:
        args.append('--allow-empty')
    rc = slash_list(args, report_stream)
    expected_rc = 0 if allow_empty else 1
    assert rc == expected_rc


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


@pytest.mark.parametrize('relative', [True, False])
def test_slash_list_tests(suite, suite_test, relative):
    suite.debug_info = False
    path = suite.commit()
    report_stream = StringIO()
    args = [path]
    if relative:
        args.append('--relative-paths')
    slash_list(args, report_stream)
    output_lines = {
        _strip(line)
        for line in report_stream.getvalue().splitlines()
    } - {"Tests", "Fixtures"}
    assert output_lines
    for filename in output_lines:
        assert os.path.isabs(filename) == (not relative)

def _strip(line):
    return re.sub(r'\x1b\[.+?m', '', line).strip()
