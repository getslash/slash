import itertools

from .utils import get_scope_by_name


_fixture_id = itertools.count()


class FixtureBase(object):

    def __init__(self):
        super(FixtureBase, self).__init__()
        self.id = next(_fixture_id)
        self.binding = {}

    def get_value(self, kwargs):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return None


class Fixture(FixtureBase):

    def __init__(self, store, fixture_func):
        super(Fixture, self).__init__()
        self.store = store
        self.fixture_func = fixture_func
        self.info = self.fixture_func.__slash_fixture__
        self.scope = self.info.scope

    def get_value(self, kwargs):
        return self.fixture_func(**kwargs)  # pylint: disable=star-args


class ThisFixture(FixtureBase):

    def __init__(self, store, fixture):
        super(ThisFixture, self).__init__()
        self.store = store
        self.fixture = fixture
        self.name = self.fixture.info.name
        self.scope = fixture.scope

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
        self.scope = get_scope_by_name('test')
        self.values = list(values)

    def get_value(self, kwargs):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return self.values
