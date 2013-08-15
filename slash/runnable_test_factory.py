from .metadata import Metadata

class RunnableTestFactory(object):

    @classmethod
    def generate_tests(cls):
        """
        Generates :class:`.RunnableTest` instances to run

        Do not override this method directly. Use :func:`.RunnableTestFactory._generate_tests` instead.
        """
        for index, test in enumerate(cls._generate_tests()):
            assert test.__slash__ is None
            test.__slash__ = Metadata(test, factory=cls, factory_index=index)
            yield test

    @classmethod
    def _generate_tests(cls):
        raise NotImplementedError() # pragma: no cover

    __slash_needed_contexts__ = None

