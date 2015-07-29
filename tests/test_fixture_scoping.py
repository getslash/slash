import collections
import itertools
import random
from contextlib import contextmanager
from uuid import uuid1

import pytest
import slash
from slash._compat import iteritems, StringIO
from slash.core.fixtures.fixture_store import FixtureStore
from slash.core.fixtures.utils import get_scope_by_name, get_scope_name_by_scope

from .utils.code_formatter import CodeFormatter


def test_fixture_scopes(fixture_tree):
    with fixture_tree.testing_scope('session'):
        for i in range(3):
            with fixture_tree.testing_scope('module'):
                for i in range(5):
                    with fixture_tree.testing_scope('test'):
                        fixture_tree.check_values()

Structure = collections.namedtuple(
    'Structure', ['required', 'graph', 'scopes'])

_FLAT_STRUCTURE = Structure(
    required=[1, 2, 3],
    graph={1: [], 2: [], 3: []},
    scopes={},
)

_FLAT_STRUCTURE_WITH_UNRELATED = Structure(
    required=[1, 2, 3],
    graph={1: [], 2: [], 3: [], 4: []},
    scopes={},
)

_DEPENDENT_STRUCTURE = Structure(
    required=[1, 2, 3],
    graph={1: [3], 2: [1], 3: []},
    scopes={},
)

_DEPENDENT_STRUCTURE_WITH_UNRELATED = Structure(
    required=[1, 2, 3],
    graph={1: [3], 2: [1], 3: [], 4: [2], 5: [1]},
    scopes={},
)

_MODULE_SCOPED = Structure(
    required=[1, 2, 3],
    graph={1: [], 2: [], 3: []},
    scopes={1: 'module', 2: 'module'},
)

_DEPENDENT_MIXED_SCOPES = Structure(
    required=[1, 2, 3],
    graph={1: [2], 2: [3], 3: []},
    scopes={3: 'session', 2: 'module'},
)


@pytest.fixture(params=[
    _FLAT_STRUCTURE,
    _FLAT_STRUCTURE_WITH_UNRELATED,
    _DEPENDENT_STRUCTURE,
    _DEPENDENT_STRUCTURE_WITH_UNRELATED,
    _MODULE_SCOPED,
    _DEPENDENT_MIXED_SCOPES,
])
def structure(request):
    return request.param


@pytest.fixture
def fixture_tree(fixture_store, structure):
    returned = FixtureTree(fixture_store, structure)
    return returned


@pytest.fixture
def fixture_store():
    return FixtureStore()


class FixtureTree(object):

    def __init__(self, fixture_store, structure):
        super(FixtureTree, self).__init__()
        self._structure = structure
        self._cleanups_made = set()
        self._fixture_store = fixture_store
        self._fixtures = {}
        self._fixture_namegen = ('fixture_{0:05}'.format(x)
                                 for x in itertools.count(1000))
        self._required_names = []
        self._populate_fixtures()
        self._values = {}

    def check_values(self):
        values = self._fixture_store.get_fixture_dict(self._required_names)
        for required_name in self._required_names:
            assert values[required_name] is not None
            expected_value = self._values[required_name]
            assert values[required_name] == expected_value

        assert not (set(self._fixtures) - set(self._required_names)
                    ).intersection(self._values), 'Non-necessary fixtures unexpectedly initialized!'

    def check_value(self, name, value):
        assert self._values[name] == value

    def make_value(self, name):
        assert name not in self._values, 'Fixture generated more than once! (scope={0})'.format(
            get_scope_name_by_scope(self._fixtures[name].__slash_fixture__.scope))
        value = str(uuid1())
        self._values[name] = value
        return value

    def cleanup(self, name):
        assert name not in self._cleanups_made
        self._cleanups_made.add(name)

    @contextmanager
    def testing_scope(self, scope):
        self._fixture_store.push_scope(scope)
        yield
        self._fixture_store.pop_scope(scope, in_failure=False, in_interruption=False)
        scope_id = get_scope_by_name(scope)
        for fixture_name, fixture in iteritems(self._fixtures):
            if fixture.__slash_fixture__.scope <= scope_id:
                if fixture_name in self._values:
                    assert fixture_name in self._cleanups_made
                    self._cleanups_made.remove(fixture_name)
                    self._values.pop(fixture_name)
        assert not self._cleanups_made, 'Unknown cleanups called'

    def _populate_fixtures(self):
        assert not self._fixtures

        graph = self._structure.graph

        key_to_fixture_name = dict((key, next(self._fixture_namegen))
                                   for key in graph)

        stack = list(self._structure.graph)

        while stack:
            fixture_key = stack.pop()
            dependent_keys = graph[fixture_key]
            unresolved = [k for k in dependent_keys if key_to_fixture_name[k]
                          not in self._fixtures]
            if unresolved:
                stack.append(fixture_key)
                stack.extend(unresolved)
                continue

            fixture_name = key_to_fixture_name[fixture_key]
            if fixture_name in self._fixtures:
                continue

            fixture = self._fixtures[fixture_name] = self._construct_fixture(
                fixture_name,
                scope=self._structure.scopes.get(fixture_key, 'test'),
                dependent_names=[key_to_fixture_name[k] for k in dependent_keys])
            self._fixture_store.add_fixture(fixture)

        self._fixture_store.resolve()
        self._required_names.extend(key_to_fixture_name[k]
                                    for k in self._structure.required)

    def _construct_fixture(self, name, scope, dependent_names):
        buff = StringIO()
        code = CodeFormatter(buff)
        code.writeln(
            'def {0}(this, {1}):'.format(name, ', '.join(dependent_names)))
        with code.indented():
            for dependent_name in dependent_names:
                code.writeln(
                    'tree.check_value({0!r}, {0})'.format(dependent_name))
            code.writeln('@this.add_cleanup')
            code.writeln('def cleanup():')
            with code.indented():
                code.writeln('tree.cleanup({0!r})'.format(name))
            code.writeln('return tree.make_value({0!r})'.format(name))
        globs = {'tree': self}
        exec(buff.getvalue(), globs)
        return slash.fixture(scope=scope)(globs[name])

@pytest.fixture(autouse=True)
def non_null_ctx(request):
    slash.ctx.push_context()
    request.addfinalizer(slash.ctx.pop_context)
