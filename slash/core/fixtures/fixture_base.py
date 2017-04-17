class FixtureBase(object):

    info = None
    keyword_arguments = None
    parametrization_ids = None
    names = None

    def get_value(self, kwargs, active_fixture):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return None  # pragma: no cover

    def resolve(self, store):
        if self.keyword_arguments is None:
            self.keyword_arguments = self._resolve(store)

    def _resolve(self, store):
        raise NotImplementedError()  # pragma: no cover
