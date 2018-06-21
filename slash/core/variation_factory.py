import collections
import itertools

from orderedset import OrderedSet

from .variation import Variation
from .._compat import OrderedDict, izip, xrange
from ..exceptions import FixtureException
from ..utils.python import get_arguments
from .fixtures.parameters import iter_parametrization_fixtures
from .fixtures.fixture import Fixture
from .fixtures.parameters import Parametrization
from .fixtures.utils import nofixtures


class VariationFactory(object):

    """Helper class to produce variations, while properly naming the needed fixtures to help identifying tests
    """

    def __init__(self, fixture_store):
        super(VariationFactory, self).__init__()
        self._store = fixture_store
        self._autouse_fixtures = list(fixture_store.iter_autouse_fixtures_in_namespace())
        self._needed_fixtures = list(self._autouse_fixtures)

        self._arg_name_bindings = OrderedDict()
        self._param_name_bindings = OrderedDict()
        self._known_value_strings = collections.defaultdict(dict)

    def add_needed_fixture_id(self, fixture_id):
        self._needed_fixtures.append(self._store.get_fixture_by_id(fixture_id))

    def add_needed_fixtures_from_method(self, method):
        self._add_needed_fixtures_from_function(method)

    def add_needed_fixtures_from_function(self, func):
        self._add_needed_fixtures_from_function(func)

    def _add_needed_fixtures_from_function(self, func):

        if isinstance(func, tuple):
            namespace, func = func
        else:
            namespace = None

        if nofixtures.is_marked(func):
            return

        args = get_arguments(func)

        parametrizations = {}
        for name, param in iter_parametrization_fixtures(func):
            # make sure the parametrization is in the store
            self._store.ensure_known_parametrization(param)
            parametrizations[name] = param

            self._needed_fixtures.append(param)

        for argument in args:
            fixture = parametrizations.get(argument.name, None)
            if fixture is None:
                try:
                    fixture = self._store.get_fixture_by_argument(argument)
                except FixtureException as e:
                    raise type(e)('Loading {0.__code__.co_filename}:{0.__name__}: {1}'.format(func, e))


            self._needed_fixtures.append(fixture)

            arg_name = argument.name
            if namespace is not None:
                arg_name = '{}:{}'.format(namespace, arg_name)

            self._populate_param_name_bindings(arg_name, fixture)
            self._arg_name_bindings[arg_name] = fixture

        for fixture in self._autouse_fixtures:
            self._populate_param_name_bindings(fixture.info.name, fixture, prefix='::')

    def _populate_param_name_bindings(self, arg_name, fixture_or_param, prefix=''):
        visited = {fixture_or_param.info.id}
        stack = [(prefix + arg_name, fixture_or_param)]
        while stack:
            name, fixture = stack.pop()
            if isinstance(fixture, Fixture):
                for sub_name, obj in fixture.keyword_arguments.items():
                    if obj.info.id in visited:
                        continue
                    visited.add(obj.info.id)
                    stack.append(('{}.{}'.format(name, sub_name), obj))
            elif isinstance(fixture, Parametrization):
                self._param_name_bindings[name] = fixture
            else:
                raise NotImplementedError() # pragma: no cover

    def iter_variations(self):
        needed_ids = OrderedSet()
        self._needed_fixtures.sort(key=lambda x: x.info.scope, reverse=True)
        for fixture in self._needed_fixtures:
            needed_ids.update(self._store.get_all_needed_fixture_ids(fixture))

        parametrizations = [self._store.get_fixture_by_id(param_id) for param_id in needed_ids]
        if not needed_ids:
            yield Variation(self._store, {}, {})
            return
        for value_indices in itertools.product(*(xrange(len(p.values)) for p in parametrizations)):
            yield self._build_variation(parametrizations, value_indices)

    def _build_variation(self, parametrizations, value_indices):
        value_index_by_id = {}
        for param, param_index in izip(parametrizations, value_indices):
            value_index_by_id[param.info.id] = param_index

        return Variation(self._store, value_index_by_id, self._param_name_bindings)
