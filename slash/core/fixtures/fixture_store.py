import itertools

from ..._compat import iteritems
from ...exceptions import (CyclicFixtureDependency, InvalidFixtureScope,
                           UnknownFixtures, UnresolvedFixtureStore)
from .fixture import Fixture, ThisFixture, Parametrization
from .utils import get_parametrization, get_scope_by_name


class FixtureStore(object):

    def __init__(self):
        super(FixtureStore, self).__init__()
        self._contexts = [Context(self)]
        self._cleanups_by_scope = {}

    def push_context(self):
        self._contexts.append(Context(self, parent=self._contexts[-1]))

    def pop_context(self):
        return self._contexts.pop(-1)

    def add_cleanup(self, scope, cleanup):
        self._cleanups_by_scope.setdefault(scope, []).append(cleanup)

    def begin_scope(self, scope):
        scope = get_scope_by_name(scope)

    def end_scope(self, scope):
        scope = get_scope_by_name(scope)
        cleanups = self._cleanups_by_scope.get(scope, [])
        while cleanups:
            cleanups.pop(-1)()

    def add_fixture(self, fixture_func):
        fixture_info = fixture_func.__slash_fixture__
        fixture_object = Fixture(self, fixture_func)
        current_context = self._contexts[-1]
        current_context.fixture_id_by_name[fixture_info.name] = fixture_object.id
        current_context.fixture_by_id[fixture_object.id] = fixture_object
        current_context.unresolved.add(fixture_object.id)
        return fixture_func

    def get_fixture_by_name(self, name):
        return self._contexts[-1].get_fixture_by_name(name)

    def get_fixture_by_id(self, fixture_id):
        return self._contexts[-1].get_fixture_by_id(fixture_id)

    def get_fixture_dict(self, required_names, variation=None):
        if any(ctx.unresolved for ctx in self._contexts):
            raise UnresolvedFixtureStore()

        returned = {}
        values = {}

        if variation is not None:
            values.update(variation)

        for required_name in required_names:
            fixture = self.get_fixture_by_name(required_name)
            self._fill_fixture_value(required_name, fixture, values)
            returned[required_name] = values[fixture.id]
        return returned

    def iter_dicts(self, required_names):
        for variation in self.iter_variation(required_names):
            yield self.get_fixture_dict(required_names, variation)

    def iter_variation(self, names):
        fixtures = self._expand_fixtures_by_names(names)
        fixture_ids = []
        pivots = []
        for fixture in fixtures:
            variations = fixture.get_variations()
            if not variations:
                continue
            fixture_ids.append(fixture.id)
            pivots.append(variations)

        if not pivots:
            yield {}
            return

        for combination in itertools.product(*pivots):  # pylint: disable=star-args
            yield dict(zip(fixture_ids, combination))

    def _expand_fixtures_by_names(self, names):
        returned = []
        for name in names:
            returned.extend(
                self._expand_fixtures(self.get_fixture_by_name(name)))
        return returned

    def _expand_fixtures(self, fixture):
        yield fixture
        for _, fixture_id in iteritems(fixture.binding):
            for x in self._expand_fixtures(self.get_fixture_by_id(fixture_id)):
                yield x

    def _fill_fixture_value(self, name, fixture, values):

        fixture_value = values.get(fixture.id, _NO_VALUE)
        if fixture_value is _BUSY:
            raise CyclicFixtureDependency(
                'Fixture {0!r} is a part of a dependency cycle!'.format(name))

        if fixture_value is not _NO_VALUE:
            return

        values[fixture.id] = _BUSY

        kwargs = {}
        for required_name, fixture_id in iteritems(fixture.binding):
            self._fill_fixture_value(
                required_name, self.get_fixture_by_id(fixture_id), values)
            kwargs[required_name] = values[fixture_id]

        values[fixture.id] = fixture.get_value(kwargs)

    def resolve(self):
        self._contexts[-1].resolve()

class Context(object):

    def __init__(self, store, parent=None):
        super(Context, self).__init__()
        self._store = store
        self._parent = parent
        self.fixture_by_id = {}
        self.fixture_id_by_name = {}
        self.unresolved = set()

    def resolve(self):
        for fixture_id in list(self.unresolved):
            self._resolve_fixture(self.fixture_by_id[fixture_id])
            self.unresolved.discard(fixture_id)

        if self._parent is not None:
            self._parent.resolve()

    def get_fixture_by_name(self, name):
        while self is not None:
            fixture_id = self.fixture_id_by_name.get(name, _NO_VALUE)
            if fixture_id is _NO_VALUE:
                self = self._parent
                continue
            return self.get_fixture_by_id(fixture_id)
        raise LookupError('Fixture {0} not found!'.format(name))

    def get_fixture_by_id(self, fixture_id):
        while self is not None:
            fixture = self.fixture_by_id.get(fixture_id, _NO_VALUE)
            if fixture is _NO_VALUE:
                self = self._parent
                continue
            return fixture
        raise LookupError('Fixture not found!')

    def _resolve_fixture(self, fixture):
        assert not fixture.binding

        binding = {}

        for parameter_name, values in iteritems(get_parametrization(fixture.fixture_func)):
            p = Parametrization(self, parameter_name, values)
            self.fixture_by_id[p.id] = p
            binding[parameter_name] = p.id

        if 'this' in fixture.info.required_args:
            meta_fixture = ThisFixture(self._store, fixture)
            self.fixture_by_id[meta_fixture.id] = meta_fixture
            binding['this'] = meta_fixture.id

        for required_arg_name in fixture.info.required_args:
            if required_arg_name in binding:
                continue
            try:
                needed = self.get_fixture_by_name(required_arg_name)
            except LookupError:
                raise UnknownFixtures(
                    'Unknown fixture: {0!r} (used from fixture {1!r}'.format(required_arg_name, fixture.info.name))
            binding[required_arg_name] = needed.id

        for name, fixture_id in iteritems(binding):
            needed = self.get_fixture_by_id(fixture_id)
            if needed.scope < fixture.scope:
                raise InvalidFixtureScope('Fixture {0} is dependent on {1}, which has a smaller scope ({2} > {3})'.format(
                    fixture.info.name, name, fixture.scope, needed.scope))

        fixture.binding.update(binding)


_BUSY = object()

_NO_VALUE = object()
