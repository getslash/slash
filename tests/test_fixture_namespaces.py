from __future__ import print_function

import functools
from contextlib import contextmanager

import slash

from .utils import run_tests_assert_success


def test_fixture_is_override():
    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.fixture
        def fixture1():
            pass

        outer = fixture1

        with s.fixture_store.new_namespace_context():

            @s.fixture_store.add_fixture
            @slash.fixture
            def fixture1():     # pylint: disable=function-redefined
                pass

            inner = fixture1

            s.fixture_store.resolve()

        outer = s.fixture_store.get_fixture_by_id(outer.__slash_fixture__.id)
        inner = s.fixture_store.get_fixture_by_id(inner.__slash_fixture__.id)

        assert outer != inner

        assert inner.is_override()
        assert not outer.is_override()


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
