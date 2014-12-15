from ..utils.python import getargspec
from .fixtures.parameters import (bound_parametrizations_context,
                                  get_parametrization_fixtures)
from .requirements import get_requirements
from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory


class FunctionTest(RunnableTest):

    def __init__(self, function, fixture_store, fixture_namespace, variation):
        super(FunctionTest, self).__init__()
        self._func = function
        self._parametrizations = set(f.name for f in get_parametrization_fixtures(self._func))
        self._func_args = [arg_name for arg_name in getargspec(self._func).args if arg_name not in self._parametrizations]
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._variation = variation

    def run(self):
        with bound_parametrizations_context(self._variation):
            self._fixture_store.activate_autouse_fixtures_in_namespace(self._fixture_namespace)
            kwargs = self._fixture_store.get_fixture_dict(self._func_args, namespace=self._fixture_namespace)
            self._func(**kwargs)  # pylint: disable=star-args

    def get_requirements(self):
        return get_requirements(self._func)


class FunctionTestFactory(RunnableTestFactory):

    def __init__(self, file_path, factory_name, module_name, func):
        super(FunctionTestFactory, self).__init__(file_path=file_path, factory_name=factory_name)
        self.func = func

    def _generate_tests(self, fixture_store):
        namespace = fixture_store.get_current_namespace()
        for variation in fixture_store.iter_parametrization_variations(funcs=[self.func]):
            address = '({0})'.format(variation.representation) if variation else None
            yield address, FunctionTest(self.func, fixture_store, namespace, variation)
