import itertools
from sentinels import NOTHING

from ..._compat import iteritems, itervalues
from ...exceptions import (CyclicFixtureDependency, UnresolvedFixtureStore)
from ...utils.python import getargspec
from .fixture import Fixture
from .utils import get_scope_by_name
from .namespace import Namespace
from .parameters import get_parametrization_fixtures, Parametrization


class FixtureStore(object):

    def __init__(self):
        super(FixtureStore, self).__init__()
        self._namespaces = [Namespace(self)]
        self._unresolved_fixture_ids = set()
        self._fixtures_by_fixture_info = {}
        self._fixtures_by_id = {}
        self._values_by_id = {}
        self._cleanups_by_scope = {}

    def push_namespace(self):
        self._namespaces.append(Namespace(self, parent=self._namespaces[-1]))

    def pop_namespace(self):
        return self._namespaces.pop(-1)

    def get_current_namespace(self):
        return self._namespaces[-1]

    def add_cleanup(self, scope, cleanup):
        assert isinstance(scope, int)
        self._cleanups_by_scope.setdefault(scope, []).append(cleanup)

    def begin_scope(self, scope):
        scope = get_scope_by_name(scope)

    def end_scope(self, scope):
        scope = get_scope_by_name(scope)
        cleanups = self._cleanups_by_scope.get(scope, [])
        for fixture_id, fixture in iteritems(self._fixtures_by_id):
            if fixture.scope <= scope:
                self._values_by_id.pop(fixture_id, None)
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

    def get_fixture_dict(self, required_names, namespace=None):

        if namespace is None:
            namespace = self.get_current_namespace()

        returned = {}

        for required_name in required_names:
            fixture = namespace.get_fixture_by_name(required_name)
            self._fill_fixture_value(required_name, fixture)
            returned[required_name] = self._values_by_id[fixture.info.id]
        return returned

    def iter_parameterization_variations(self, names=(), fixtures=(), fixture_ids=(), funcs=(), methods=()):
        needed_fixtures = []
        for name in names:
            needed_fixtures.append(self.get_fixture_by_name(name))
        needed_fixtures.extend(fixtures)
        for fixture_id in fixture_ids:
            needed_fixtures.append(self.get_fixture_by_id(fixture_id))

        for is_method, func in itertools.chain(itertools.izip(itertools.repeat(False), funcs),
                                               itertools.izip(itertools.repeat(True), methods)):
            for fixture in get_parametrization_fixtures(func):
                assert fixture.info.id not in self._fixtures_by_id or self._fixtures_by_id[fixture.info.id] is fixture
                self._fixtures_by_id[fixture.info.id] = fixture
                needed_fixtures.append(fixture)
            needed_fixtures.extend(self._get_needed_fixture_from_func(func, is_method=is_method))

        param_ids = self._get_all_dependent_parametrization_ids_from_names(needed_fixtures)
        if not param_ids:
            yield {}
            return
        for combination in itertools.product(*(self._fixtures_by_id[id].values for id in param_ids)):
            yield dict(zip(param_ids, combination))

    def _get_needed_fixture_from_func(self, func, is_method):
        parametrization = set(p.name for p in get_parametrization_fixtures(func))
        args = getargspec(func).args
        if is_method:
            args = args[1:]
        for name in args:
            if name not in parametrization:
                yield self.get_fixture_by_name(name)

    def _get_all_dependent_parametrization_ids_from_names(self, fixtures):
        returned = set()
        assert isinstance(fixtures, list)

        while fixtures:
            f = fixtures.pop(-1)
            if isinstance(f, Parametrization):
                returned.add(f.info.id)
            if f.parametrization_ids is not None:
                returned.update(f.parametrization_ids)
            if f.fixture_kwargs:
                for needed_fixture_id in itervalues(f.fixture_kwargs):
                    fixtures.append(self.get_fixture_by_id(needed_fixture_id))
        return returned

    def _fill_fixture_value(self, name, fixture):

        fixture_value = self._values_by_id.get(fixture.info.id, NOTHING)
        if fixture_value is _BUSY:
            raise CyclicFixtureDependency(
                'Fixture {0!r} is a part of a dependency cycle!'.format(name))

        if fixture_value is not NOTHING:
            return

        self._values_by_id[fixture.info.id] = _BUSY

        kwargs = {}

        if fixture.fixture_kwargs is None:
            raise UnresolvedFixtureStore('Fixture {0} is unresolved!'.format(name))

        for required_name, fixture_id in iteritems(fixture.fixture_kwargs):
            self._fill_fixture_value(
                required_name, self.get_fixture_by_id(fixture_id))
            kwargs[required_name] = self._values_by_id[fixture_id]

        self._values_by_id[fixture.info.id] = fixture.get_value(kwargs)

    def resolve(self):
        while self._unresolved_fixture_ids:
            fixture = self._fixtures_by_id[self._unresolved_fixture_ids.pop()]
            fixture.resolve(self)


_BUSY = object()
