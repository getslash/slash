# pylint: disable=redefined-outer-name
from __future__ import print_function

import os
import shutil
from tempfile import mkdtemp

import pytest
from slash.utils import suite_files


def test_iter_suite_paths_files_abspaths(filename, paths):
    with open(filename, 'w') as f:
        f.write('\n'.join(paths))

    assert [p for p, _ in suite_files.iter_suite_file_paths([filename])] == paths


def test_iter_suite_paths_files_relpath(filename, paths):
    with open(filename, 'w') as f:
        for path in paths:
            relpath = os.path.relpath(path, os.path.dirname(filename))
            assert not os.path.isabs(relpath)
            f.write(relpath)
            f.write('\n')

    assert [p for p, _ in suite_files.iter_suite_file_paths([filename])] == [os.path.abspath(p) for p in paths]


def test_suite_files(suite, suite_test, suite_file):  # pylint: disable=unused-argument
    suite.run(args=[])


def test_suite_file_with_filter(suite, suite_test, suite_file):
    path = suite.commit()
    with suite_file.open('w') as f:
        print(path, '# filter:', suite_test.name, file=f)
    suite.run(args=[])


def test_parse_filter_string():
    suite_entry = suite_files._parse_path_filter_and_repeat('some_path.py # filter: bla')  # pylint: disable=protected-access
    assert suite_entry.path == 'some_path.py'
    assert suite_entry.matcher is not None
    assert suite_entry.matcher.matches('bla')
    assert not suite_entry.matcher.matches('blooop')


@pytest.mark.parametrize("string", [
    'some_path.py #',
    'some_path.py # bbb',
    'some_path.py#'
])
def test_parse_filter_string_no_filter(string):
    suite_entry = suite_files._parse_path_filter_and_repeat(string)  # pylint: disable=protected-access
    assert suite_entry.path == 'some_path.py'
    assert suite_entry.matcher is None


def test_iter_suite_file_paths_nested_filter(tmpdir):

    test_filename = '/some/test/file.py'
    suite_file1 = tmpdir.join('file1.txt')
    suite_file2 = tmpdir.join('file2.txt')

    with suite_file1.open('w') as f:
        print(suite_file2, '# filter: not blue', file=f)

    with suite_file2.open('w') as f:
        print(test_filename, '# filter: green', file=f)

    [(item, matcher)] = suite_files.iter_suite_file_paths([str(suite_file1)])
    assert item == test_filename
    assert matcher.matches('green')
    assert not matcher.matches('blue')
    assert not matcher.matches('green blue')


def test_parse_repeat_string():
    suite_entry = suite_files._parse_path_filter_and_repeat('some_path.py # repeat: 5')  # pylint: disable=protected-access
    assert suite_entry.path == 'some_path.py'
    assert suite_entry.matcher is None
    assert suite_entry.repeat == 5


@pytest.mark.parametrize("string", [
    'some_path.py # filter: bla, repeat: 5',
    'some_path.py # repeat: 5, filter: bla',
])
def test_parse_repeat_string_with_filter(string):
    suite_entry = suite_files._parse_path_filter_and_repeat(string)  # pylint: disable=protected-access
    assert suite_entry.path == 'some_path.py'
    assert suite_entry.matcher is not None
    assert suite_entry.matcher.matches('bla')
    assert not suite_entry.matcher.matches('blooop')
    assert suite_entry.matcher is not None
    assert suite_entry.repeat == 5


@pytest.fixture
def suite_file(tmpdir, suite, suite_test, config_override):
    path = suite.commit()
    suite_file_path = tmpdir.join('suite.txt')
    with suite_file_path.open('w') as f:
        f.write(suite_test.get_full_address(path))
    suite.deselect_all(exclude=[suite_test])
    config_override('run.suite_files', [str(suite_file_path)])
    return suite_file_path


@pytest.mark.parametrize('use_relpath', [True, False])
def test_files_containing_files(filename, paths, use_relpath):
    filename2 = os.path.join(os.path.dirname(filename), 'file2.txt')

    with open(filename2, 'w') as f:
        f.write('\n'.join(paths[::-1]))

    if use_relpath:
        filename2 = os.path.basename(filename2)

    with open(filename, 'w') as f:
        f.write('\n'.join(paths))
        f.write('\n')
        f.write(filename2)

    assert [p for p, _ in suite_files.iter_suite_file_paths([filename])] == paths + paths[::-1]


def test_slash_run_with_suite_file(suite, suite_test, tmpdir):
    path = suite.commit()
    with tmpdir.join('suitefile').open('w') as suite_file:  # pylint: disable=redefined-outer-name
        _fill_suite_file(path, [suite_test], suite_file=suite_file)

    for t in suite:
        if t is not suite_test:
            t.expect_deselect()

    suite.run(args=[], additional_args=['-f', suite_file.name])


def test_slash_run_with_suite_file_invalid_test(suite, suite_test, tmpdir):
    path = suite.commit()

    additional_test = suite[0]
    assert additional_test is not suite_test

    with tmpdir.join('suitefile').open('w') as suite_file:  # pylint: disable=redefined-outer-name
        _fill_suite_file(path, [additional_test], suite_file=suite_file, corrupt=False)
        _fill_suite_file(path, [suite_test], suite_file=suite_file, corrupt=True)

    for t in suite:
        t.expect_deselect()

    summary = suite.run(args=[], additional_args=['-f', suite_file.name], expect_session_errors=True)
    assert summary.exit_code != 0
    assert 'Cannot find test' in summary.get_console_output()
    assert 'CORRUPT' in summary.get_console_output()


def _fill_suite_file(root_path, tests, suite_file, corrupt=False):  # pylint: disable=redefined-outer-name
    for test in tests:
        suite_file.write(test.get_full_address(root_path))
        if corrupt:
            suite_file.write('CORRUPT')
        suite_file.write('\n')


@pytest.fixture
def filename(tmpdir):
    return str(tmpdir.join('filename.txt'))


@pytest.fixture
def paths(request, tmpdir, use_relpath_for_dir): # pylint: disable=redefined-outer-name
    basenames = ['file{0}.py'.format(i) for i in range(10)]
    basenames.extend(['file100.py:SomeClass',
                      'file101.py:Someclass.test_method'])
    returned = [os.path.join(os.path.abspath(str(tmpdir)), b) for b in basenames]

    if use_relpath_for_dir:
        dirname = str(tmpdir.join('dirname'))
        os.makedirs(dirname)
    else:
        dirname = mkdtemp()

        @request.addfinalizer
        def cleanup():  # pylint: disable=unused-variable
            shutil.rmtree(dirname)
    returned.append(dirname)

    return returned


@pytest.fixture(params=[True, False])
def use_relpath_for_dir(request):
    return request.param
