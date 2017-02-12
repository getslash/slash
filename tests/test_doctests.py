from __future__ import print_function

import doctest
import os

import pytest
import slash

_HERE = os.path.abspath(os.path.dirname(__file__))
_DOCS_ROOT = os.path.abspath(os.path.join(_HERE, "..", "doc"))


def test_sphinx_doctest(doctest_path):  # pylint: disable=redefined-outer-name
    globs = {'print_function': print_function, 'slash': slash}
    result = doctest.testfile(doctest_path, module_relative=False, globs=globs)
    assert not result.failed

assert os.path.exists(_DOCS_ROOT)
_DOCTEST_PATHS = list(os.path.join(path, filename)
                      for path, _, filenames in os.walk(_DOCS_ROOT)
                      for filename in filenames
                      if filename.endswith(".rst"))
_README_PATH = os.path.join(_HERE, '..', 'README.md')


@pytest.fixture(params=_DOCTEST_PATHS + [_README_PATH])
def doctest_path(request):
    return request.param
