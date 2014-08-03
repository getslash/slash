import inspect

from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory


class FunctionTest(RunnableTest):

    def __init__(self, function, fixture_store, fixture_namespace, variation):
        super(FunctionTest, self).__init__()
        self._func = function
        self._required_fixtures = inspect.getargspec(self._func).args
        for name in self._required_fixtures:
            assert name in fixture_namespace
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._variation = variation

    def run(self):
        kwargs = self._fixture_store.get_fixture_dict(self._required_fixtures, self._variation, self._fixture_namespace)
        self._func(**kwargs)  # pylint: disable=star-args


class FunctionTestFactory(RunnableTestFactory):

    def __init__(self, file_path, factory_name, func):
        super(FunctionTestFactory, self).__init__(file_path, factory_name)
        self.func = func

    def _generate_tests(self, fixture_store):
        namespace = fixture_store.get_current_namespace()
        names = inspect.getargspec(self.func).args
        for variation in fixture_store.iter_variations(names):
            yield None, FunctionTest(self.func, fixture_store, namespace, variation)
