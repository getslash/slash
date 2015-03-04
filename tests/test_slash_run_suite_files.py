import os
import shutil
import tempfile
from tempfile import mkdtemp

import pytest
from slash.frontend.slash_run import _iter_suite_file_paths


def test_iter_suite_paths_files_abspaths(filename, paths):
    with open(filename, 'w') as f:
        f.write('\n'.join(paths))

    assert list(_iter_suite_file_paths([filename])) == paths

def test_iter_suite_paths_files_relpath(filename, paths):
    with open(filename, 'w') as f:
        for path in paths:
            relpath = os.path.relpath(path, os.path.dirname(filename))
            assert not os.path.isabs(relpath)
            f.write(relpath)
            f.write('\n')

    assert list(_iter_suite_file_paths([filename])) == [os.path.abspath(p) for p in paths]

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

    assert list(_iter_suite_file_paths([filename])) == paths + paths[::-1]


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
