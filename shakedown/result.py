import sys

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
    def is_just_failure(self):
        """Indicates this is a pure failure, without errors involved"""
        return self.is_failure() and not self.is_error()
    def is_skip(self):
        return bool(self._skips)
    def is_success(self):
        return self._finished and not self._errors and not self._failures and not self._skips
    def is_finished(self):
        return self._finished
    def mark_finished(self):
        self._finished = True
    def add_error(self):
        self._errors.append(sys.exc_info()[1])
    def add_failure(self):
        self._failures.append(sys.exc_info()[1])
    def add_skip(self, reason):
        self._skips.append(reason)
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
        return self._count(Result.is_success)
    def get_num_errors(self):
        return self._count(Result.is_error)
    def get_num_failures(self):
        return self._count(Result.is_just_failure)
    def get_num_skipped(self):
        return self._count(Result.is_skip)
    def _count(self, pred):
        returned = 0
        for result in self:
            if pred(result):
                returned += 1
        return returned
