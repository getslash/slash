import itertools


class BalancedStrategy(object):

    def __init__(self, max_tests_per_file=5, max_tests_per_class=3):
        super(BalancedStrategy, self).__init__()
        self._max_tests_per_file = max_tests_per_file
        self._max_tests_per_class = max_tests_per_class
        self._type_gen = itertools.cycle(['function', 'method'])

    def get_test_type(self):
        return next(self._type_gen)

    def get_file_for_test(self, suite):
        candidate = suite.get_last_file()
        if candidate is not None and candidate.get_num_tests() < self._max_tests_per_file:
            return candidate
        return suite.add_file()

    def get_class_for_test(self, file):
        candidate = file.get_last_class()
        if candidate is not None and candidate.get_num_tests() < self._max_tests_per_class:
            return candidate
        return file.add_class()
