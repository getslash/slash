from __future__ import print_function

import os
import shutil
from tempfile import mkdtemp

import pytest
from slash.utils import suite_files, pattern_matching


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


def test_suite_files(suite, suite_test, suite_file):
    suite.run(args=[])


def test_suite_file_with_filter(suite, suite_test, suite_file):
    path = suite.commit()
    with suite_file.open('w') as f:
        print(path, '# filter:', suite_test.name, file=f)
    suite.run(args=[])


def test_parse_filter_string():
    path, filter = suite_files._parse_path_and_filter('some_path.py # filter: bla')
    assert path == 'some_path.py'
    assert filter is not None
    assert filter.matches('bla')
    assert not filter.matches('blooop')


@pytest.mark.parametrize("string", [
    'some_path.py #',
    'some_path.py # bbb',
    'some_path.py#',
])
def test_parse_filter_string_no_filter(string):
    path, filter = suite_files._parse_path_and_filter(string)
    assert path == 'some_path.py'
    assert filter is None


def test_iter_suite_file_paths_nested_filter(tmpdir):

    test_filename = '/some/test/file.py'
    suite_file1 = tmpdir.join('file1.txt')
    suite_file2 = tmpdir.join('file2.txt')

    with suite_file1.open('w') as f:
        print(suite_file2, '# filter: not blue', file=f)

    with suite_file2.open('w') as f:
        print(test_filename, '# filter: green', file=f)

    [(item, filter)] = suite_files.iter_suite_file_paths([str(suite_file1)])
    assert item == test_filename
    assert filter.matches('green')
    assert not filter.matches('blue')
    assert not filter.matches('green blue')


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


@pytest.fixture
def filename(tmpdir):
    return str(tmpdir.join('filename.txt'))


@pytest.fixture
def paths(request, tmpdir, use_relpath_for_dir):
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
        def cleanup():
            shutil.rmtree(dirname)
    returned.append(dirname)

    return returned


@pytest.fixture(params=[True, False])
def use_relpath_for_dir(request):
    return request.param
