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

    def get_requirements(self):
        raise NotImplementedError() # pragma: no cover

    def get_required_fixture_objects(self):
        raise NotImplementedError() # pragma: no cover

    def get_fixture_namespace(self):
        return self._fixture_namespace

    def __repr__(self):
        return '<Runnable test {0!r}>'.format(self.__slash__)
