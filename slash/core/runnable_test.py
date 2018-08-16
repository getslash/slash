import copy
from .tagging import NO_TAGS

class RunnableTest(object):

    """
    This class is meant to serve as a base class to any test that can
    actually be executed by the Slash runner.
    """
    __slash__ = None

    def __init__(self, fixture_store, fixture_namespace, variation):
        super(RunnableTest, self).__init__()
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._variation = variation

    def clone(self):
        returned = copy.copy(self)
        for copied_attr in ('_variation', '__slash__'):
            setattr(returned, copied_attr, copy.copy(getattr(returned, copied_attr)))
        return returned

    @property
    def id(self):
        return self.__slash__.id

    def get_variation(self):
        return self._variation

    def get_address_in_factory(self):
        raise NotImplementedError() # pragma: no cover

    def run(self):
        """
        This method is meant to be overriden by derived classes to actually
        perform the test logic
        """
        raise NotImplementedError()  # pragma: no cover

    def get_tags(self):
        return NO_TAGS

    def get_test_function(self):
        raise NotImplementedError() # pragma: no cover

    def get_unmet_requirements(self):
        returned = []
        for req in self.get_requirements():
            is_met, reason = req.is_met()
            if not is_met:
                returned.append((req, reason))
        return returned

    def _get_fixture_tags(self):
        tags = NO_TAGS
        for fixture in self.get_required_fixture_objects():
            tags += fixture.get_tags(self._fixture_store)
        return tags

    def _get_fixtures_requirements(self):
        fixture_requirements = [item for fixture in self.get_required_fixture_objects() for item in fixture.get_requirements(self._fixture_store)]
        autouse_fixture_requirements = [item for fixture in self._fixture_store.iter_autouse_fixtures_in_namespace(self.get_fixture_namespace()) \
                            for item in fixture.get_requirements(self._fixture_store)]
        return list(set(fixture_requirements + autouse_fixture_requirements))

    def get_requirements(self):
        raise NotImplementedError() # pragma: no cover

    def get_required_fixture_objects(self):
        raise NotImplementedError() # pragma: no cover

    def get_fixture_namespace(self):
        return self._fixture_namespace

    def __repr__(self):
        return '<Runnable test {!r}>'.format(self.__slash__)
