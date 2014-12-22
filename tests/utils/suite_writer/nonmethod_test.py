from contextlib import contextmanager

from .test import Test


class NonMethodTest(Test):

    cls = None

    def __init__(self, suite, file):
        super(NonMethodTest, self).__init__(suite, file)

    def is_method_test(self):
        return False
