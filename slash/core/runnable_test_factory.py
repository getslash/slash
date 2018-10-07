import sys

from .metadata import Metadata
from ..exceptions import SlashInternalError


class RunnableTestFactory(object):

    def __init__(self, param=None):
        super(RunnableTestFactory, self).__init__()
        self._param = param
        self._factory_name = self._filename = self._module_name = None

    def set_factory_name(self, name):
        self._factory_name = name

    def get_factory_name(self):
        returned = self._factory_name
        if returned is None:
            returned = self._param.__name__
        assert returned
        return returned

    def get_class_name(self):
        return None

    def set_module_name(self, module_name):
        self._module_name = module_name

    def get_module_name(self):
        returned = self._module_name
        if returned is None:
            returned = self._param.__module__
        assert returned
        return returned

    def set_filename(self, filename):
        self._filename = filename

    def get_filename(self):
        returned = self._filename
        if returned is None:
            returned = sys.modules[self._param.__module__].__file__
        if returned.endswith('.pyc'):
            returned = returned[:-1]
        assert returned
        return returned

    def generate_tests(self, fixture_store):
        """
        Generates :class:`.RunnableTest` instances to run

        Do not override this method directly. Use :func:`.RunnableTestFactory._generate_tests` instead.
        """
        for test in self._generate_tests(fixture_store):
            if test.__slash__ is not None:
                raise SlashInternalError("{} has Metadata before generating it".format(test))

            test.__slash__ = Metadata(self, test)
            yield test

    def _generate_tests(self, fixture_store):
        raise NotImplementedError()  # pragma: no cover
