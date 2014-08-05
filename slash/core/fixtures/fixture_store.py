import itertools
from sentinels import NOTHING

from ..._compat import iteritems, itervalues
from ...exceptions import (CyclicFixtureDependency, UnresolvedFixtureStore)
from .fixture import Fixture
from .utils import get_scope_by_name
from .namespace import Namespace


class FixtureStore(object):

    def __init__(self):
        super(FixtureStore, self).__init__()
        self._namespaces = [Namespace(self)]
        self._unresolved_fixture_ids = set()
        self._fixtures_by_fixture_info = {}
        self._fixtures_by_id = {}
        self._cleanups_by_scope = {}

    def push_namespace(self):
        self._namespaces.append(Namespace(self, parent=self._namespaces[-1]))

    def pop_namespace(self):
        return self._namespaces.pop(-1)

    def get_current_namespace(self):
        return self._namespaces[-1]

    def add_cleanup(self, scope, cleanup):
        self._cleanups_by_scope.setdefault(scope, []).append(cleanup)

    def begin_scope(self, scope):
        scope = get_scope_by_name(scope)

    def end_scope(self, scope):
        scope = get_scope_by_name(scope)
        cleanups = self._cleanups_by_scope.get(scope, [])
        while cleanups:
            cleanups.pop(-1)()

    def add_fixtures_from_dict(self, d):
        for name, thing in iteritems(d):
            fixture_info = getattr(thing, '__slash_fixture__', None)
            if fixture_info is None:
                continue
            self.get_current_namespace().add_name(
                name, self.add_fixture(thing).__slash_fixture__.id)

    def add_fixture(self, fixture_func):
        fixture_info = fixture_func.__slash_fixture__
        existing_fixture = self._fixtures_by_id.get(fixture_info.id)
        if existing_fixture is not None:
            return existing_fixture.fixture_func
        fixture_object = Fixture(self, fixture_func)
        current_namespace = self._namespaces[-1]
        current_namespace.add_name(fixture_info.name, fixture_info.id)
        self.register_fixture_id(fixture_object)
        return fixture_func

    def register_fixture_id(self, f):
        assert f.info.id not in self._fixtures_by_id
        self._fixtures_by_id[f.info.id] = f
        self._unresolved_fixture_ids.add(f.info.id)

    def get_fixture_by_name(self, name):
        return self._namespaces[-1].get_fixture_by_name(name)

    def get_fixture_by_id(self, fixture_id):
        return self._fixtures_by_id[fixture_id]

    def get_fixture_dict(self, required_names, variation=None, namespace=None):

        if namespace is None:
            namespace = self.get_current_namespace()

        returned = {}
        values = {}

        if variation is not None:
            values.update(variation)

        for required_name in required_names:
            fixture = namespace.get_fixture_by_name(required_name)
            self._fill_fixture_value(required_name, fixture, values)
            returned[required_name] = values[fixture.info.id]
        return returned

    def iter_dicts(self, required_names):
        for variation in self.iter_variations(required_names):
            yield self.get_fixture_dict(required_names, variation)

    def iter_variations(self, names):
        fixtures = self._get_all_dependent_fixtures_from_names(names)
        fixture_ids = []
        pivots = []
        for fixture in fixtures:
            variations = fixture.get_variations()
            if not variations:
                continue
            fixture_ids.append(fixture.info.id)
            pivots.append(variations)

        if not pivots:
            yield {}
            return

        for combination in itertools.product(*pivots):  # pylint: disable=star-args
            yield dict(zip(fixture_ids, combination))

    def _get_all_dependent_fixtures_from_names(self, names):
        returned = set()
        stack = [self.get_fixture_by_name(name) for name in names]

        while stack:
            needed = stack.pop(-1)
            returned.add(needed)
            for needed_id in itervalues(needed.fixture_kwargs):
                stack.append(self.get_fixture_by_id(needed_id))
        return returned

    def _fill_fixture_value(self, name, fixture, values):

        fixture_value = values.get(fixture.info.id, NOTHING)
        if fixture_value is _BUSY:
            raise CyclicFixtureDependency(
                'Fixture {0!r} is a part of a dependency cycle!'.format(name))

        if fixture_value is not NOTHING:
            return

        values[fixture.info.id] = _BUSY

        kwargs = {}

        if fixture.fixture_kwargs is None:
            raise UnresolvedFixtureStore('Fixture {0} is unresolved!'.format(name))

        for required_name, fixture_id in iteritems(fixture.fixture_kwargs):
            self._fill_fixture_value(
                required_name, self.get_fixture_by_id(fixture_id), values)
            kwargs[required_name] = values[fixture_id]

        values[fixture.info.id] = fixture.get_value(kwargs)

    def resolve(self):
        while self._unresolved_fixture_ids:
            fixture = self._fixtures_by_id[self._unresolved_fixture_ids.pop()]
            fixture.resolve(self)


_BUSY = object()
