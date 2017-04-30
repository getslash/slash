import itertools

from .test import Test


class MethodTest(Test):  # pylint: disable=abstract-method

    def __init__(self, suite, cls):
        super(MethodTest, self).__init__(suite, cls.file)
        self.cls = cls

    def is_method_test(self):
        return True

    def _get_argument_strings(self):
        return itertools.chain(['self'], super(MethodTest, self)._get_argument_strings())
