from .metadata import Metadata

class RunnableTestFactory(object):

    @classmethod
    def generate_tests(cls, file_path, factory_name):
        """
        Generates :class:`.RunnableTest` instances to run

        Do not override this method directly. Use :func:`.RunnableTestFactory._generate_tests` instead.
        """
        for address, test in cls._generate_tests():
            assert test.__slash__ is None
            test.__slash__ = Metadata(cls, test, file_path, factory_name, address)
            yield test

    @classmethod
    def _generate_tests(cls):
        raise NotImplementedError() # pragma: no cover

    __slash_needed_contexts__ = None

