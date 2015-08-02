from sentinels import NOTHING
from numbers import Number

from ..._compat import itervalues
from ...exceptions import UnknownFixtures


class Namespace(object):

    def __init__(self, store, parent=None):
        super(Namespace, self).__init__()
        self._store = store
        self._parent = parent
        self._fixture_names = {}

    def iter_fixtures(self):
        while self is not None:
            for fixture_id in itervalues(self._fixture_names):
                yield self._store.get_fixture_by_id(fixture_id)
            self = self._parent

    def __repr__(self):
        return 'Fixtures: {0}'.format(', '.join(self._iter_fixture_names()) or '**None**')

    def _iter_fixture_names(self):
        while self is not None:
            for k in self._fixture_names:
                yield k
            self = self._parent

    def get_fixture_by_name(self, name):
        while self is not None:
            fixture_id = self._fixture_names.get(name, NOTHING)
            if fixture_id is NOTHING:
                self = self._parent
                continue
            return self._store.get_fixture_by_id(fixture_id)
        raise UnknownFixtures('Fixture {0!r} not found!'.format(name))

    def add_name(self, name, fixture_id):
        assert isinstance(fixture_id, Number)
        assert name not in self._fixture_names or self._fixture_names[
            name] == fixture_id
        self._fixture_names[name] = fixture_id
