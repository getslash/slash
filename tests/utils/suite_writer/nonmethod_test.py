from .test import SuiteWriterTest


class NonMethodTest(SuiteWriterTest):  # pylint: disable=abstract-method

    cls = None

    def __init__(self, suite, file):  # pylint: disable=useless-super-delegation
        super(NonMethodTest, self).__init__(suite, file)

    def is_method_test(self):
        return False
