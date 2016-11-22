# pylint: disable=redefined-outer-name, unused-argument
from __future__ import print_function

import functools
import os
import random
from uuid import uuid4

import pytest

import slash


def test_normal_sorting(test_dir, names):
    assert get_file_names(load(test_dir)) == names

def test_custom_ordering(test_dir, names, indices):
    @slash.hooks.tests_loaded.register # pylint: disable=no-member
    def tests_loaded(tests):                # pylint: disable=unused-variable
        for (test, new_index) in zip(tests, indices):
            test.__slash__.set_sort_key(new_index)
    assert get_file_names(load(test_dir)) == _sorted_by_indices(names, indices)

################################################################################
## Utils and fixtures

def get_file_names(tests):
    returned = []
    for t in tests:
        file_path = t.__slash__.file_path
        assert os.path.isabs(file_path)
        returned.append(os.path.join(
            os.path.basename(os.path.dirname(file_path)),
            os.path.basename(file_path)))
    return returned

def load(source):
    with slash.Session():
        return slash.loader.Loader().get_runnables([source])

@pytest.fixture
def test_dir(tmpdir, names, indices):
    returned = tmpdir.join(str(uuid4()))
    indices = range(len(names))[::-1]
    for index, name in zip(indices, names):
        with returned.join(name).open('w', ensure=True) as f:
            _print = functools.partial(print, file=f)
            _print('import slash')
            _print('@slash.tag("index", {})'.format(index))
            _print('def test_something():')
            _print('    pass')
    return str(returned)

@pytest.fixture
def names():
    return ['a/test_a_b.py', 'a/test_b_a.py', 'b/test_a_a.py', 'b/test_a_b.py']

def _sorted_by_indices(items, indices):
    returned = [None for _ in items]
    for index, item in zip(indices, items):
        returned[index] = item
    return returned

def _randomized(l):
    indices = list(range(len(l)))
    random.shuffle(indices)
    return [l[index] for index in indices]

@pytest.fixture(params=[reversed, _randomized])
def indices(request, names):
    return [names.index(name) for name in request.param(names)]
