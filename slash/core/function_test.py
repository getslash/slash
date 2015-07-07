from .._compat import xrange

from .fixtures.parameters import bound_parametrizations_context
from .requirements import get_requirements
from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory
from .tagging import get_tags


class FunctionTest(RunnableTest):

    def __init__(self, function, fixture_store, fixture_namespace, variation):
        super(FunctionTest, self).__init__()
        self._func = function
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._variation = variation

    def get_tags(self):
        return get_tags(self._func)

    def run(self):
        with bound_parametrizations_context(self._variation):
            self._fixture_store.activate_autouse_fixtures_in_namespace(namespace=self._fixture_namespace)
            self._fixture_store.call_with_fixtures(
                self._func, namespace=self._fixture_namespace,
                is_method=False
            )

    def get_requirements(self):
        return get_requirements(self._func)

    def get_required_fixture_objects(self):
        return self._fixture_store.get_required_fixture_objects(self._func, namespace=self._fixture_namespace, is_method=False)


class FunctionTestFactory(RunnableTestFactory):

    def __init__(self, func):
        super(FunctionTestFactory, self).__init__(func)
        self.func = func

    def _generate_tests(self, fixture_store):
        namespace = fixture_store.get_current_namespace()
        for variation in fixture_store.iter_parametrization_variations(funcs=[self.func]):
            address = '({0})'.format(variation.representation) if variation else None
            for _ in xrange(self._get_num_repetitions(self.func)):
                yield address, FunctionTest(self.func, fixture_store, namespace, variation)
