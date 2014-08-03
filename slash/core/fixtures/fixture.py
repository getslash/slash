import itertools

from ..._compat import iteritems
from ...exceptions import UnknownFixtures, InvalidFixtureScope

from .namespace import Namespace
from .utils import get_scope_by_name, FixtureInfo, get_parametrization


_fixture_id = itertools.count()


class FixtureBase(object):

    info = None
    fixture_kwargs = None

    def __init__(self):
        super(FixtureBase, self).__init__()

    def get_value(self, kwargs):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return None

    def resolve(self, store):
        if self.fixture_kwargs is None:
            self.fixture_kwargs = self._resolve(store)

    def _resolve(self, store):
        raise NotImplementedError() # pragma: no cover


class Fixture(FixtureBase):

    fixture_kwargs = None

    def __init__(self, store, fixture_func):
        super(Fixture, self).__init__()
        self.store = store
        self.fixture_func = fixture_func
        self.info = self.fixture_func.__slash_fixture__
        self.scope = self.info.scope
        self.namespace = Namespace(store, store.get_current_namespace())

    def get_value(self, kwargs):
        return self.fixture_func(**kwargs)  # pylint: disable=star-args

    def _resolve(self, store):
        if self.fixture_kwargs is not None:
            return
        kwargs = {}

        for parameter_name, values in iteritems(get_parametrization(self.fixture_func)):
            p = Parametrization(store, parameter_name, values)
            store.register_fixture_id(p)
            self.namespace.add_name(parameter_name, p.info.id)

        if 'this' in self.info.required_args:
            meta_fixture = ThisFixture(store, self)
            store.register_fixture_id(meta_fixture)
            self.namespace.add_name('this', meta_fixture.info.id)

        for name in self.info.required_args:
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


class Parametrization(FixtureBase):

    def __init__(self, store, name, values):
        super(Parametrization, self).__init__()
        self.store = store
        self.name = name
        self.info = FixtureInfo(name=name)
        self.scope = get_scope_by_name('test')
        self.values = list(values)

    def get_value(self, kwargs):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return self.values

    def _resolve(self, store):
        return {}
