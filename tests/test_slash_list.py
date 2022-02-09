from __future__ import print_function
import munch
import functools
import os
import re

from slash.frontend.slash_list import slash_list
from io import StringIO
from .utils.suite_writer import Suite

import pytest


def _slash_list(argv, *args, **kwargs):
    return slash_list(munch.Munch(argv=argv), *args, **kwargs)


@pytest.mark.parametrize('flag', ["--only-fixtures", "--only-tests", None])
def test_slash_list(suite, flag):
    suite.debug_info = False
    _ = suite.slashconf.add_fixture()
    path = suite.commit()
    report_stream = StringIO()

    args = [path]
    if flag is not None:
        args.append(flag)
    _slash_list(args, report_stream)
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
    rc = _slash_list(args, report_stream)
    expected_rc = 0 if allow_empty else 1
    assert rc == expected_rc


def test_slash_list_tests_without_tags(suite):
    suite.debug_info = False
    path = suite.commit()
    report_stream = StringIO()
    args = [path, '--show-tags', '--no-output']
    _slash_list(args, report_stream)
    output = report_stream.getvalue()
    assert not output


@pytest.mark.parametrize('should_show_tags', [True, False])
def test_slash_list_tests_with_or_without_tags(suite, should_show_tags, suite_test):
    suite_test.add_decorator('slash.tag("bla")')
    suite.debug_info = False
    path = suite.commit()
    report_stream = StringIO()
    args = [path, '--only-tests']
    if should_show_tags:
        args.append('--show-tags')
    _slash_list(args, report_stream)
    output = report_stream.getvalue()
    assert ('Tags' in output) == (should_show_tags)


@pytest.mark.parametrize('relative', [True, False])
def test_slash_list_tests_relative_or_not(suite, relative):
    suite.debug_info = False
    path = suite.commit()
    report_stream = StringIO()
    args = [path]
    if relative:
        args.append('--relative-paths')
    _slash_list(args, report_stream)
    output_lines = {
        _strip(line)
        for line in report_stream.getvalue().splitlines()
    } - {"Tests", "Fixtures"}
    assert output_lines
    for filename in output_lines:
        assert os.path.isabs(filename) == (not relative)


@pytest.mark.parametrize('show_duplicates,expected_tests_num', [(True, 2), (False, 1)])
def test_slash_list_suite_duplicate_tests(tmpdir, show_duplicates, expected_tests_num):
    with tmpdir.join('test_file.py').open('w') as f:
        _print = functools.partial(print, file=f)
        _print('def test_function():')
        _print('    pass')

    with tmpdir.join('suitefile').open('w') as suite_file:
        _print = functools.partial(print, file=suite_file)
        _print('{}:test_function{}'.format(f.name, ''))
        _print('{}:test_function{}'.format(f.name, ''))

    args = ['-f', suite_file.name, '--only-tests']
    if show_duplicates:
        args.append('--show-duplicates')
    report_stream = StringIO()
    result = _slash_list(args, report_stream=report_stream)
    assert result == 0
    returned_tests = report_stream.getvalue().splitlines()
    assert len(returned_tests) == expected_tests_num
    assert set(returned_tests) == {'{}:test_function'.format(f.name)}


@pytest.mark.parametrize('invalid', [None, 'test', 'method'])
@pytest.mark.parametrize('allow_empty', [True, False])
def test_slash_list_suite_file_incorrect_names(tmpdir, invalid, allow_empty):

    with tmpdir.join('test_file.py').open('w') as f:
        _print = functools.partial(print, file=f)

        _print('import slash')
        _print('class TestSomething(slash.Test):')
        _print('    def test_method(self):')
        _print('        pass')
        _print()
        _print('def test_function():')
        _print('    pass')

    function_name_remainder = method_name_remainder = ''

    if invalid == 'test':
        function_name_remainder = 'f'
    elif invalid == 'method':
        method_name_remainder = 'm'
    elif invalid is not None:
        raise NotImplementedError() # pragma: no cover

    error_stream = StringIO()

    with tmpdir.join('suitefile').open('w') as suite_file:
        _print = functools.partial(print, file=suite_file)
        _print('{}:TestSomething.test_method{}'.format(f.name, method_name_remainder))
        _print('{}:test_function{}'.format(f.name, function_name_remainder))

    args = ['-f', suite_file.name]
    if allow_empty:
        args.append('--allow-empty') # make sure allow-empty does not affect invalid name lookup
    result = _slash_list(args, error_stream=error_stream)

    if invalid is None:
        assert result == 0
    else:
        assert result != 0
        assert 'Could not load tests' in error_stream.getvalue()
        if invalid == 'test':
            assert 'test_functionf' in error_stream.getvalue()
        elif invalid == 'method':
            assert 'test_methodm' in error_stream.getvalue()
        else:
            raise NotImplementedError() # pragma: no cover


@pytest.mark.parametrize('no_tests', [True, False])
def test_slash_list_with_warnings(tmpdir, no_tests):
    with tmpdir.join('test_file.py').open('w') as fp:
        _print = functools.partial(print, file=fp)
        _print('import warnings')
        _print('from slash import hooks')

        _print()
        _print('warnings.warn("Some warning")')
        _print('@hooks.after_session_start.register')
        _print('def _warn():')
        _print('    warnings.warn("Some warning")')

        if not no_tests:
            _print()
            _print('def test_me():')
            _print('    pass')

    error_stream = StringIO()
    args = [fp.name, '--warnings-as-errors']
    if no_tests:
        args.append('--allow-empty')
    result = _slash_list(args, error_stream=error_stream)

    errors = error_stream.getvalue()
    assert 'Could not load tests' not in errors
    assert result != 0


def test_slash_list_with_filtering(tmpdir):
    with tmpdir.join('test_file.py').open('w') as fp:
        _print = functools.partial(print, file=fp)
        _print()
        _print('def test_a():')
        _print('    pass')
        _print('')
        _print('def test_b():')
        _print('    pass')
        _print('')
        _print('def test_c():')
        _print('    pass')

    report_stream = StringIO()
    args = [fp.name, '-k', 'not _b', '--only-tests']
    result = _slash_list(args, report_stream=report_stream)
    assert result == 0

    listed_tests = _strip(report_stream.getvalue()).splitlines()
    assert listed_tests == ['{}:{}'.format(fp.name, test_name) for test_name in ('test_a', 'test_c')]


def _strip(line):
    return re.sub(r'\x1b\[.+?m', '', line).strip()
