import sys

import collections

from ..._compat import iteritems, itervalues, OrderedDict, reraise
from ...ctx import context as slash_context
from ...exception_handling import handling_exceptions
from ...exceptions import CyclicFixtureDependency, UnresolvedFixtureStore
from ...utils.python import getargspec
from .fixture import Fixture
from .namespace import Namespace
from .parameters import Parametrization, get_parametrizations
from .utils import get_scope_by_name, nofixtures
from .variation import VariationFactory
from .active_fixture import ActiveFixture

class FixtureStore(object):

    def __init__(self):
        super(FixtureStore, self).__init__()
        self._namespaces = [Namespace(self)]
        self._unresolved_fixture_ids = set()
        self._fixtures_by_id = {}
        self._fixtures_by_fixture_info = {}
        self._active_fixtures_by_scope = collections.defaultdict(OrderedDict)
        self._computing = set()
        self._all_needed_parametrization_ids_by_fixture_id = {}

    def get_active_fixture(self, fixture):
        return self._active_fixtures_by_scope[fixture.info.scope].get(fixture.info.id)

    def call_with_fixtures(self, test_func, namespace, is_method):

        if not nofixtures.is_marked(test_func):
            arg_names = self.get_required_fixture_names(test_func, is_method=is_method)
            kwargs = self.get_fixture_dict(arg_names, namespace)
        else:
            kwargs = {}

        return test_func(**kwargs)

    def get_required_fixture_names(self, test_func, is_method):
        skip_names = set(name for p in get_parametrizations(test_func) for name in p.names)
        arg_names = [name for name in getargspec(test_func).args if name not in skip_names]
        if is_method:
            arg_names = arg_names[1:]
        return arg_names

    def get_required_fixture_objects(self, test_func, namespace, is_method):
        names = self.get_required_fixture_names(test_func, is_method=is_method)
        return set(itervalues(self.get_fixture_dict(names, namespace=namespace, get_values=False)))

    def __iter__(self):
        return itervalues(self._fixtures_by_id)

    def push_namespace(self):
        self._namespaces.append(Namespace(self, parent=self._namespaces[-1]))

    def pop_namespace(self):
        return self._namespaces.pop(-1)

    def get_current_namespace(self):
        return self._namespaces[-1]

    def get_all_needed_parametrization_ids(self, fixtureobj):
        if self._unresolved_fixture_ids:
            raise UnresolvedFixtureStore()
        if isinstance(fixtureobj, Parametrization):
            return frozenset([fixtureobj.info.id])
        returned = self._all_needed_parametrization_ids_by_fixture_id.get(fixtureobj.info.id)
        if returned is None:
            returned = self._compute_all_needed_parametrization_ids(fixtureobj)
            self._all_needed_parametrization_ids_by_fixture_id[fixtureobj.info.id] = returned
        return returned

    def iter_autouse_fixtures_in_namespace(self, namespace=None):
        if namespace is None:
            namespace = self.get_current_namespace()
        for fixture in namespace.iter_fixtures():
            if fixture.info.autouse:
                yield fixture

    def activate_autouse_fixtures_in_namespace(self, namespace):
        for fixture in self.iter_autouse_fixtures_in_namespace(namespace):
            _ = self.get_fixture_value(fixture)

    def _compute_all_needed_parametrization_ids(self, fixtureobj):
        stack = [(fixtureobj.info.id, [fixtureobj.info.id], set([fixtureobj.info.id]))]
        returned = set()
        while stack:
            fixture_id, path, visited = stack.pop()
            if fixture_id in self._all_needed_parametrization_ids_by_fixture_id:
                returned.update(self._all_needed_parametrization_ids_by_fixture_id[fixture_id])
                continue
            fixture = self._fixtures_by_id[fixture_id]
            if fixture.parametrization_ids:
                returned.update(fixture.parametrization_ids)
            if fixture.fixture_kwargs:
                for needed_id in itervalues(fixture.fixture_kwargs):
                    if needed_id in visited:
                        self._raise_cyclic_dependency_error(fixtureobj, path, needed_id)
                    stack.append((needed_id, path + [needed_id], visited | set([needed_id])))
        return frozenset(returned)

    def _raise_cyclic_dependency_error(self, fixtureobj, path, new_id):
        raise CyclicFixtureDependency(
            'Cyclic fixture dependency detected in {0}: {1}'.format(
                fixtureobj.info.func.__code__.co_filename,
                ' -> '.join(self._fixtures_by_id[f_id].info.name
                            for f_id in path + [new_id])))

    def push_scope(self, scope):
        scope = get_scope_by_name(scope)

    def pop_scope(self, scope, in_failure, in_interruption): # pylint: disable=unused-argument
        if in_interruption:
            return
        scope = get_scope_by_name(scope)
        for s, active_fixtures in iteritems(self._active_fixtures_by_scope):
            if s <= scope:
                for active_fixture in list(active_fixtures.values())[::-1]:
                    with handling_exceptions(swallow=True):
                        self._deactivate_fixture(active_fixture.fixture)
                assert not active_fixtures

    def ensure_known_parametrization(self, parametrization):
        if parametrization.info.id not in self._fixtures_by_id:
            self._fixtures_by_id[parametrization.info.id] = parametrization

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

    def get_fixture_dict(self, required_names, namespace=None, get_values=True, skip_names=frozenset()):
        returned = {}

        if namespace is None:
            namespace = self.get_current_namespace()

        for required_name in required_names:
            if required_name in skip_names:
                continue
            fixture = namespace.get_fixture_by_name(required_name)
            if get_values:
                fixture = self.get_fixture_value(fixture, name=required_name)
            returned[required_name] = fixture
        return returned

    def get_fixture_value(self, fixture, name=None):
        if name is None:
            name = fixture.info.name

        value = self._fill_fixture_value(name, fixture)
        return value

    def iter_parametrization_variations(self, fixture_ids=(), funcs=(), methods=()):

        variation_factory = VariationFactory(self)
        for fixture_id in fixture_ids:
            variation_factory.add_needed_fixture_id(fixture_id)

        for func in funcs:
            variation_factory.add_needed_fixtures_from_function(func)

        for method in methods:
            variation_factory.add_needed_fixtures_from_method(method)

        return variation_factory.iter_variations()

    def _fill_fixture_value(self, name, fixture):
        if fixture.info.id in self._computing:
            raise CyclicFixtureDependency(
                'Fixture {0!r} is a part of a dependency cycle!'.format(name))

        active_fixture = self.get_active_fixture(fixture)

        if active_fixture is not None:
            return active_fixture.value

        self._computing.add(fixture.info.id)
        try:
            fixture_value = self._activate_fixture(fixture)
        except:
            exc_info = sys.exc_info()
            self._deactivate_fixture(fixture)
            reraise(*exc_info)
        finally:
            self._computing.discard(fixture.info.id)

        return fixture_value

    def _activate_fixture(self, fixture):
        active_fixture = ActiveFixture(fixture)

        kwargs = {}

        if fixture.fixture_kwargs is None:
            raise UnresolvedFixtureStore('Fixture {0} is unresolved!'.format(fixture.info.name))

        for required_name, fixture_id in iteritems(fixture.fixture_kwargs):
            kwargs[required_name] = self._fill_fixture_value(
                required_name, self.get_fixture_by_id(fixture_id))


        assert fixture.info.id not in self._active_fixtures_by_scope[fixture.info.scope]
        self._active_fixtures_by_scope[fixture.info.scope][fixture.info.id] = active_fixture
        prev_context_fixture = slash_context.fixture
        slash_context.fixture = active_fixture
        try:
            returned = active_fixture.value = fixture.get_value(kwargs, active_fixture)
        finally:
            slash_context.fixture = prev_context_fixture
        return returned

    def _deactivate_fixture(self, fixture):
        # in most cases it will be the last active fixture in its scope
        active = self._active_fixtures_by_scope[fixture.info.scope].pop(fixture.info.id, None)
        if active is not None:
            active.do_cleanups()

    def resolve(self):
        while self._unresolved_fixture_ids:
            fixture = self._fixtures_by_id[self._unresolved_fixture_ids.pop()]
            fixture.resolve(self)
