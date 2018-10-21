import collections
import sys
from contextlib import contextmanager

from slash import ctx
import logbook
from orderedset import OrderedSet

from ..._compat import OrderedDict, iteritems, itervalues, reraise
from ...ctx import context as slash_context
from ...exception_handling import handling_exceptions
from ...exceptions import CyclicFixtureDependency, UnresolvedFixtureStore, UnknownFixtures, InvalidFixtureName
from ...utils.python import get_arguments
from ..variation_factory import VariationFactory
from ..test import is_valid_test_name
from .active_fixture import ActiveFixture
from .fixture import Fixture
from .namespace import Namespace
from .parameters import Parametrization, iter_parametrization_fixtures
from .utils import (get_real_fixture_name_from_argument, get_scope_by_name,
                    nofixtures)

_logger = logbook.Logger(__name__)

class FixtureStore(object):

    def __init__(self):
        super(FixtureStore, self).__init__()
        self._namespaces = [Namespace(self)]
        self._unresolved_fixture_ids = set()
        self._fixtures_by_id = {}
        self._fixtures_by_fixture_info = {}
        self._active_fixtures_by_scope = collections.defaultdict(OrderedDict)
        self._active_fixture_dependencies = {} # maps fixture id to the frozenset of (param_id, variation index)
        self._computing = set()
        self._all_needed_parametrization_ids_by_fixture_id = {}
        self._known_fixture_ids = collections.defaultdict(dict) # maps fixture ids to known combinations

    def get_active_fixture(self, fixture):
        return self._active_fixtures_by_scope[fixture.info.scope].get(fixture.info.id)

    def _compute_id(self, variation, p):
        if isinstance(p, Parametrization):
            return variation.param_value_indices[p.info.id]
        combination = frozenset((f.info.id, self._compute_id(variation, f))
                                for f in self.iter_all_needed_fixture_objects(p))
        known = self._known_fixture_ids[p.info.id]
        return known.setdefault(combination, len(known))

    def iter_all_needed_fixture_objects(self, fixtureobj):
        for fid in self.get_all_needed_fixture_ids(fixtureobj):
            yield self.get_fixture_by_id(fid)

    def iter_active_fixtures(self):
        for _, fixtures in self._active_fixtures_by_scope.items():
            for f in fixtures.values():
                yield f

    def call_with_fixtures(self, test_func, namespace, trigger_test_start=False, trigger_test_end=False):
        if not nofixtures.is_marked(test_func):
            fixture_names = self.get_required_fixture_names(test_func)
            kwargs = self.get_fixture_dict(fixture_names, namespace)
            used_fixtures_decorator_names = getattr(test_func, '__extrafixtures__', None)
            if used_fixtures_decorator_names is not None:
                used_fixture_names_only = set(used_fixtures_decorator_names) - set(fixture_names)
                for name in used_fixture_names_only:
                    self.get_fixture_value(namespace.get_fixture_by_name(name))
        else:
            kwargs = {}

        if trigger_test_start:
            for fixture in self.iter_active_fixtures():
                fixture.call_test_start()

        try:
            return test_func(**kwargs)
        finally:
            if trigger_test_end:
                for fixture in self.iter_active_fixtures():
                    with handling_exceptions(swallow=True):
                        fixture.call_test_end()

    def get_required_fixture_names(self, test_func):
        """Returns a list of fixture names needed by test_func.

        Each element returned is either a string or a tuple of (required_name, real_name)
        """
        skip_names = {name for name, _ in iter_parametrization_fixtures(test_func)}
        returned = []
        for argument in get_arguments(test_func):
            if argument.name in skip_names:
                continue
            real_name = get_real_fixture_name_from_argument(argument)
            if real_name == argument.name:
                returned.append(real_name)
            else:
                returned.append((argument.name, real_name))
        return returned

    def get_required_fixture_objects(self, test_func, namespace):
        names = self.get_required_fixture_names(test_func)
        assert isinstance(names, list)
        return set(itervalues(self.get_fixture_dict(names, namespace=namespace, get_values=False)))

    def resolve_name(self, parameter_name, start_point, namespace=None):

        if namespace is None:
            namespace = self.get_current_namespace()

        parts = parameter_name.split('.')[::-1]

        if not parts:
            raise UnknownFixtures(parameter_name)

        while parts:
            current_name = parts.pop()
            param_fixtures = dict(iter_parametrization_fixtures(start_point))
            if current_name in param_fixtures:
                if parts: # we cannot decend further than a parameter
                    raise UnknownFixtures(parameter_name)
                start_point = param_fixtures[current_name]
            else:
                start_point = self.get_fixture_by_name(current_name, namespace=namespace)
                namespace = start_point.namespace
        return start_point

    def __iter__(self):
        return itervalues(self._fixtures_by_id)

    def push_namespace(self):
        self._namespaces.append(Namespace(self, parent=self._namespaces[-1]))

    def pop_namespace(self):
        return self._namespaces.pop(-1)

    @contextmanager
    def new_namespace_context(self):
        self.push_namespace()
        try:
            yield
        finally:
            self.pop_namespace()

    def get_current_namespace(self):
        return self._namespaces[-1]

    def get_all_needed_fixture_ids(self, fixtureobj):
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
        returned = OrderedSet()
        while stack:
            fixture_id, path, visited = stack.pop()
            if fixture_id in self._all_needed_parametrization_ids_by_fixture_id:
                returned.update(self._all_needed_parametrization_ids_by_fixture_id[fixture_id])
                continue
            fixture = self._fixtures_by_id[fixture_id]
            if fixture.parametrization_ids:
                assert isinstance(fixture.parametrization_ids, OrderedSet)
                returned.update(fixture.parametrization_ids)
            if fixture.keyword_arguments:
                for needed in itervalues(fixture.keyword_arguments):
                    if needed.is_parameter():
                        continue
                    needed_id = needed.info.id
                    if needed_id in visited:
                        self._raise_cyclic_dependency_error(fixtureobj, path, needed_id)
                    stack.append((needed_id, path + [needed_id], visited | set([needed_id])))
        return returned

    def _raise_cyclic_dependency_error(self, fixtureobj, path, new_id):
        raise CyclicFixtureDependency(
            'Cyclic fixture dependency detected in {}: {}'.format(
                fixtureobj.info.func.__code__.co_filename,
                ' -> '.join(self._fixtures_by_id[f_id].info.name
                            for f_id in path + [new_id])))

    def push_scope(self, scope):
        scope = get_scope_by_name(scope)

    def pop_scope(self, scope): # pylint: disable=unused-argument
        if slash_context.result is not None and slash_context.result.is_interrupted():
            return
        scope = get_scope_by_name(scope)
        for s, active_fixtures in iteritems(self._active_fixtures_by_scope):
            if s <= scope:
                for active_fixture in reversed(list(active_fixtures.values())):
                    with handling_exceptions(swallow=True):
                        self._deactivate_fixture(active_fixture.fixture)
                assert not active_fixtures

    def ensure_known_parametrization(self, parametrization):
        if parametrization.info.id not in self._fixtures_by_id:
            self._fixtures_by_id[parametrization.info.id] = parametrization

    def add_fixtures_from_dict(self, d):
        for thing in itervalues(d):
            fixture_info = getattr(thing, '__slash_fixture__', None)
            if fixture_info is None:
                continue
            assert self.get_current_namespace() is self._namespaces[-1]
            fixture_info = self.add_fixture(thing).__slash_fixture__
            self.get_current_namespace().add_name(
                fixture_info.name, fixture_info.id)


    def add_fixture(self, fixture_func):
        fixture_info = fixture_func.__slash_fixture__
        existing_fixture = self._fixtures_by_id.get(fixture_info.id)
        if existing_fixture is not None:
            return existing_fixture.fixture_func
        if is_valid_test_name(fixture_info.name):
            raise InvalidFixtureName('Invalid fixture name: {.name}'.format(fixture_info))
        fixture_object = Fixture(self, fixture_func)
        current_namespace = self._namespaces[-1]
        current_namespace.add_name(fixture_info.name, fixture_info.id)
        self.register_fixture_id(fixture_object)
        return fixture_func

    def register_fixture_id(self, f):
        if f.info.id in self._fixtures_by_id:
            return
        self._fixtures_by_id[f.info.id] = f
        self._unresolved_fixture_ids.add(f.info.id)

    def get_fixture_by_name(self, name, namespace=None):
        if namespace is None:
            namespace = self._namespaces[-1]
        return namespace.get_fixture_by_name(name)

    def get_fixture_by_argument(self, arg):
        return self.get_fixture_by_name(get_real_fixture_name_from_argument(arg))

    def get_fixture_by_id(self, fixture_id):
        return self._fixtures_by_id[fixture_id]

    def get_fixture_dict(self, fixture_names, namespace=None, get_values=True, skip_names=frozenset()):
        returned = {}

        if namespace is None:
            namespace = self.get_current_namespace()

        for element in fixture_names:
            if isinstance(element, tuple):
                required_name, real_name = element
            else:
                required_name = real_name = element

            if required_name in skip_names:
                continue
            if element == 'this':
                continue
            fixture = namespace.get_fixture_by_name(real_name)
            if get_values:
                fixture = self.get_fixture_value(fixture, name=required_name)
            returned[required_name] = fixture
        return returned

    def get_fixture_value(self, fixture, name=None):
        if name is None:
            name = fixture.info.name

        value = self._compute_fixture_value(name, fixture)
        return value

    def get_value(self, variation, parameter_or_fixture):
        fixture_id = parameter_or_fixture.info.id

        fixtureobj = self.get_fixture_by_id(parameter_or_fixture.info.id)
        if isinstance(fixtureobj, Parametrization):
            value = parameter_or_fixture.get_value_by_index(variation.param_value_indices[fixture_id])
        else:
            value = self.get_fixture_value(parameter_or_fixture)

        return value

    def iter_parametrization_variations(self, fixture_ids=(), funcs=(), methods=()):
        if self._unresolved_fixture_ids:
            raise UnresolvedFixtureStore()

        variation_factory = VariationFactory(self)
        for fixture_id in fixture_ids:
            variation_factory.add_needed_fixture_id(fixture_id)

        for func in funcs:
            variation_factory.add_needed_fixtures_from_function(func)

        for method in methods:
            variation_factory.add_needed_fixtures_from_method(method)

        return variation_factory.iter_variations()

    def _compute_fixture_value(self, name, fixture, relative_name=None):
        if relative_name is None:
            relative_name = name

        assert not fixture.is_parameter()

        if fixture.info.id in self._computing:
            raise CyclicFixtureDependency(
                'Fixture {!r} is a part of a dependency cycle!'.format(name))
        active_fixture = self.get_active_fixture(fixture)
        if active_fixture is not None:
            if self._is_active_fixture_valid(fixture):
                _logger.trace("Fixture {} did not change", fixture)
                return active_fixture.value
            else:
                _logger.trace("Fixture {} no longer valid. Recomputing", fixture)
                self._deactivate_fixture(active_fixture.fixture)

        self._computing.add(fixture.info.id)
        try:
            fixture_value = self._call_fixture(fixture, relative_name=relative_name)
        except:
            exc_info = sys.exc_info()
            self._deactivate_fixture(fixture)
            reraise(*exc_info)
        finally:
            self._computing.discard(fixture.info.id)

        return fixture_value

    def _is_active_fixture_valid(self, fixture):
        assert fixture.info.id in self._active_fixture_dependencies, "Fixture dependencies not updated"
        new_dependencies = self._compute_fixture_dependencies(fixture)
        return new_dependencies.issubset(self._active_fixture_dependencies[fixture.info.id])

    def _compute_fixture_dependencies(self, fixture):

        param_indices = self._compute_all_needed_parametrization_ids(fixture)
        if not param_indices:
            return frozenset()

        assert ctx.session is not None, "Dependency computation requires an active session"
        variation = ctx.session.variations.get_current_variation()
        assert variation is not None, "Dependency computation requires current variation"

        return frozenset((param_id, variation.param_value_indices[param_id])
                         for param_id in self._compute_all_needed_parametrization_ids(fixture))

    def _call_fixture(self, fixture, relative_name):
        assert relative_name
        active_fixture = ActiveFixture(fixture)

        kwargs = {}

        if fixture.keyword_arguments is None:
            raise UnresolvedFixtureStore('Fixture {} is unresolved!'.format(fixture.info.name))

        for required_name, needed_fixture in iteritems(fixture.keyword_arguments):
            if needed_fixture.is_parameter():
                continue
            kwargs[required_name] = self._compute_fixture_value(
                required_name, needed_fixture,
                relative_name='{} -> {}'.format(relative_name, required_name))


        assert fixture.info.id not in self._active_fixtures_by_scope[fixture.info.scope]
        _logger.trace("Activating fixture {}...", fixture)
        self._active_fixtures_by_scope[fixture.info.scope][fixture.info.id] = active_fixture
        self._active_fixture_dependencies[fixture.info.id] = self._compute_fixture_dependencies(fixture)
        prev_context_fixture = slash_context.fixture
        slash_context.fixture = active_fixture
        try:
            returned = active_fixture.value = fixture.get_value(kwargs, active_fixture)
        finally:
            slash_context.fixture = prev_context_fixture
        _logger.trace(' -- {} = {!r}', relative_name, returned)
        return returned

    def _deactivate_fixture(self, fixture):
        # in most cases it will be the last active fixture in its scope
        active = self._active_fixtures_by_scope[fixture.info.scope].pop(fixture.info.id, None)
        self._active_fixture_dependencies.pop(fixture.info.id, None)
        if active is not None:
            active.do_cleanups()

    def resolve(self):
        while self._unresolved_fixture_ids:
            fixture = self._fixtures_by_id[self._unresolved_fixture_ids.pop()]
            fixture.resolve(self)
