import itertools
from collections import OrderedDict

from orderedset import OrderedSet

from ...exceptions import UnknownFixtures, InvalidFixtureScope, CyclicFixtureDependency

from ..._compat import ExitStack
from ...ctx import context
from .namespace import Namespace
from .parameters import iter_parametrization_fixtures
from .fixture_base import FixtureBase
from .utils import get_real_fixture_name_from_argument
from ..requirements import get_requirements
from ..tagging import get_tags, NO_TAGS, Tags

_fixture_id = itertools.count()



class Fixture(FixtureBase):

    def __init__(self, store, fixture_func):
        super(Fixture, self).__init__()
        self.fixture_func = fixture_func
        self.info = self.fixture_func.__slash_fixture__
        self.scope = self.info.scope
        self.namespace = Namespace(store, store.get_current_namespace())

    def get_tags(self, store):
        current_fixture_tags = get_tags(self.fixture_func)
        returned = current_fixture_tags.copy() if current_fixture_tags is not NO_TAGS else Tags()
        required_fixtures_tags = [fixture.get_tags(store) for fixture in store.get_required_fixture_objects(self.fixture_func, self.namespace)]
        for tags in required_fixtures_tags:
            returned.update(tags)
        return returned

    def is_parameter(self):
        return False

    def is_fixture(self):
        return True

    parametrization_ids = None

    def __repr__(self):
        return '<Function Fixture around {}>'.format(self.fixture_func)

    def is_override(self):
        parent = self.namespace.get_parent()

        while parent is not None:
            f = parent.get_fixture_by_name(self.info.name, default=None)
            if f is None:
                return False

            if f is not self:
                return True

            parent = parent.get_parent()
        return False

    def get_value(self, kwargs, active_fixture):
        if self.info.needs_this:
            assert 'this' not in kwargs
            kwargs['this'] = active_fixture
        with ExitStack() as stack:
            if context.session is not None:
                stack.enter_context(context.session.cleanups.default_scope_override(self.info.scope_name))
            return self.fixture_func(**kwargs)

    def get_requirements(self, store):
        fixture_requirements = get_requirements(self.fixture_func)
        required_fixtures = store.get_required_fixture_objects(self.fixture_func, self.namespace)
        while required_fixtures:
            fixture_requirements.extend(required_fixtures.pop().get_requirements(store))
        return fixture_requirements

    def _resolve(self, store):
        assert self.keyword_arguments is None
        assert self.parametrization_ids is None
        self.parametrization_ids = OrderedSet()
        keyword_arguments = OrderedDict()

        parametrized = set()

        for name, param in iter_parametrization_fixtures(self.fixture_func):
            store.register_fixture_id(param)
            parametrized.add(name)
            self.parametrization_ids.add(param.info.id)
            keyword_arguments[name] = param

        for param_name, arg in self.info.required_args.items():
            if param_name in parametrized:
                continue
            try:
                needed_fixture = self.namespace.get_fixture_by_name(get_real_fixture_name_from_argument(arg))

                if needed_fixture.scope < self.scope: # pylint: disable=no-member
                    raise InvalidFixtureScope('Fixture {} is dependent on {}, which has a smaller scope ({} > {})'.format(
                        self.info.name, param_name, self.scope, needed_fixture.scope)) # pylint: disable=no-member

                if needed_fixture is self:
                    raise CyclicFixtureDependency('Cyclic fixture dependency detected in {}: {} depends on itself'.format(
                        self.info.func.__code__.co_filename,
                        self.info.name))
                keyword_arguments[param_name] = needed_fixture
            except LookupError:
                raise UnknownFixtures(param_name)

        return keyword_arguments
