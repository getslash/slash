import sys
from .exceptions import TestFailed

class Result(object):
    def __init__(self, test_metadata=None):
        super(Result, self).__init__()
        self.test_metadata = test_metadata
        self._errors = []
        self._failures = []
        self._skips = []
        self._finished = False
    def is_error(self):
        return bool(self._errors)
    def is_failure(self):
        return bool(self._failures)
    def is_success(self):
        return self._finished and not self._errors and not self._failures and not self._skips
    def is_finished(self):
        return self._finished
    def mark_finished(self):
        self._finished = True
    def add_exception(self):
        _, exc_value, _ = sys.exc_info()
        if isinstance(exc_value, TestFailed):
            self.add_failure()
        else:
            self.add_error()
    def add_error(self):
        self._errors.append(sys.exc_info()[1])
    def add_failure(self):
        self._failures.append(sys.exc_info()[1])
    def get_errors(self):
        return self._errors
    def get_failures(self):
        return self._failures

class AggregatedResult(object):
    def __init__(self, result_iterator_func):
        super(AggregatedResult, self).__init__()
        self._iterator = result_iterator_func
    def __iter__(self):
        return self._iterator()
    def is_success(self):
        return all(result.is_success() for result in self._iterator())
    def get_num_successful(self):
        return count(result for result in self if result.is_success())
    def get_num_errors(self):
        return count(result for result in self if result.is_error())
    def get_num_failures(self):
        return count(result for result in self if result.is_failure() and not result.is_error())

def count(iterable):
    i = 0
    for _ in iterable:
        i += 1
    return i
