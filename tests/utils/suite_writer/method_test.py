import itertools
from contextlib import contextmanager

from .test import Test


class MethodTest(Test):

    def __init__(self, suite, cls):
        super(MethodTest, self).__init__(suite, cls.file)
        self.cls = cls

    def is_method_test(self):
        return True

    def _get_argument_names(self):
        return itertools.chain(['self'], super(MethodTest, self)._get_argument_names())
