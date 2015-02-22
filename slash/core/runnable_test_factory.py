from .markers import repeat
from .metadata import Metadata
from ..conf import config


class RunnableTestFactory(object):

    def __init__(self, file_path='', module_name='', factory_name=''):
        super(RunnableTestFactory, self).__init__()
        self.file_path = file_path
        self.module_name = module_name
        self.factory_name = factory_name

    def generate_tests(self, fixture_store):
        """
        Generates :class:`.RunnableTest` instances to run

        Do not override this method directly. Use :func:`.RunnableTestFactory._generate_tests` instead.
        """
        for address_in_factory, test in self._generate_tests(fixture_store):
            assert test.__slash__ is None
            test.__slash__ = Metadata(self, test, address_in_factory)
            yield test

    def _generate_tests(self, fixture_store):
        raise NotImplementedError()  # pragma: no cover

    def _get_num_repetitions(self, func):
        return repeat.get_value(func, 1) * config.root.run.repeat_each

