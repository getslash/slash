class FixtureBase(object):

    info = None
    fixture_kwargs = None
    parametrization_ids = None
    names = None

    def __init__(self):
        super(FixtureBase, self).__init__()

    def get_value(self, kwargs, active_fixture):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return None  # pragma: no cover

    def resolve(self, store):
        if self.fixture_kwargs is None:
            self.fixture_kwargs = self._resolve(store)

    def _resolve(self, store):
        raise NotImplementedError()  # pragma: no cover
