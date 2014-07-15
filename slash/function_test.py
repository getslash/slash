from .runnable_test import RunnableTest

class FunctionTest(RunnableTest):

    def __init__(self, function):
        super(FunctionTest, self).__init__()
        self._func = function

    def run(self):
        self._func()
