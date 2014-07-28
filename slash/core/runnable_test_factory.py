from .metadata import Metadata


class RunnableTestFactory(object):

    def __init__(self, file_path='', factory_name=''):
        super(RunnableTestFactory, self).__init__()
        self.file_path = file_path
        self.factory_name = factory_name

    def generate_tests(self):
        """
        Generates :class:`.RunnableTest` instances to run

        Do not override this method directly. Use :func:`.RunnableTestFactory._generate_tests` instead.
        """
        for address_in_factory, test in self._generate_tests():
            assert test.__slash__ is None
            test.__slash__ = Metadata(self, test, address_in_factory)
            yield test

    def _generate_tests(self):
        raise NotImplementedError()  # pragma: no cover
