from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory


class FunctionTest(RunnableTest):

    def __init__(self, function):
        super(FunctionTest, self).__init__()
        self._func = function

    def run(self):
        self._func()


class FunctionTestFactory(RunnableTestFactory):

    def __init__(self, file_path, factory_name, func):
        super(FunctionTestFactory, self).__init__(file_path, factory_name)
        self.func = func

    def _generate_tests(self):
        yield None, FunctionTest(self.func)
