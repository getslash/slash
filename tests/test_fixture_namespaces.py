from __future__ import print_function

import functools
from contextlib import contextmanager

from .utils import run_tests_assert_success

def test_fixture_namespaces(tmpdir):

    root_dir = tmpdir.join('tests')

    with _into(root_dir.join('slashconf.py')) as writeln:
        _write_fixture1(writeln)

    with _into(root_dir.join('test_something.py')) as writeln:
        _write_fixture1(writeln)

        writeln('def test_something(fixture1):')
        writeln('    pass')

    run_tests_assert_success([str(root_dir)])

def _write_fixture1(writeln):
    writeln('import slash')

    writeln('@slash.fixture')
    writeln('def fixture1():')
    writeln('    pass')



@contextmanager
def _into(f):
    with f.open('w', ensure=True) as f:
        yield functools.partial(print, file=f)
