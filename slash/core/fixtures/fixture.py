import itertools

from ...exceptions import UnknownFixtures, InvalidFixtureScope

from ...ctx import context
from .namespace import Namespace
from .parameters import get_parametrization_fixtures
from .utils import FixtureInfo
from .fixture_base import FixtureBase


_fixture_id = itertools.count()



class Fixture(FixtureBase):

    def __init__(self, store, fixture_func):
        super(Fixture, self).__init__()
        self.fixture_func = fixture_func
        self.info = self.fixture_func.__slash_fixture__
        self.scope = self.info.scope
        self.namespace = Namespace(store, store.get_current_namespace())

    def __repr__(self):
        return '<Function Fixture around {0}>'.format(self.fixture_func)

    def get_value(self, kwargs):
        return self.fixture_func(**kwargs)

    def _resolve(self, store):
        assert self.fixture_kwargs is None

        assert self.parametrization_ids is None
        self.parametrization_ids = []

        kwargs = {}
        parametrized = set()

        for parametrization_fixture in get_parametrization_fixtures(self.fixture_func):
            store.register_fixture_id(parametrization_fixture)
            parametrized.add(parametrization_fixture.name)
            self.parametrization_ids.append(parametrization_fixture.info.id)

        if 'this' in self.info.required_args:
            meta_fixture = ThisFixture(store, self)
            store.register_fixture_id(meta_fixture)
            self.namespace.add_name('this', meta_fixture.info.id)

        for name in self.info.required_args:
            if name in parametrized:
                continue
            try:
                needed_fixture = self.namespace.get_fixture_by_name(name)

                if needed_fixture.scope < self.scope:
                    raise InvalidFixtureScope('Fixture {0} is dependent on {1}, which has a smaller scope ({2} > {3})'.format(
                        self.info.name, name, self.scope, needed_fixture.scope))

                assert needed_fixture is not self
                kwargs[name] = needed_fixture.info.id
            except LookupError:
                raise UnknownFixtures(name)
        return kwargs


class ThisFixture(FixtureBase):

    def __init__(self, store, fixture):
        super(ThisFixture, self).__init__()
        assert context.session is None or store is context.session.fixture_store
        self.store = store
        self.info = FixtureInfo()
        self.fixture = fixture
        self.name = self.fixture.info.name
        self.scope = fixture.scope

    def _resolve(self, store):
        return {}

    def add_cleanup(self, func):
        self.store.add_cleanup(self.scope, func)

    def get_value(self, kwargs):
        assert not kwargs
        return self

    def __repr__(self):
        return '<This Fixture>'
