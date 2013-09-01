import itertools
import functools
import sys
from .._compat import itervalues
from ..utils.error_object import Error

class Result(object):
    def __init__(self, test_metadata=None):
        super(Result, self).__init__()
        self.test_metadata = test_metadata
        self._errors = []
        self._failures = []
        self._skips = []
        self._finished = False
        self._interrupted = False
    def is_error(self):
        return bool(self._errors)
    def is_failure(self):
        return bool(self._failures)
    def is_just_failure(self):
        """Indicates this is a pure failure, without errors involved"""
        return self.is_failure() and not self.is_error()
    def is_skip(self):
        return bool(self._skips)
    def is_success(self, allow_skips=False):
        returned = not self._errors and not self._failures and not self._interrupted
        if not allow_skips:
            returned &= not self._skips
        return returned
    def is_success_finished(self):
        return self.is_success() and self.is_finished()
    def is_finished(self):
        return self._finished
    def mark_finished(self):
        self._finished = True
    def mark_interrupted(self):
        self._interrupted = True
    def is_interrupted(self):
        return self._interrupted
    def add_error(self):
        self._errors.append(Error(sys.exc_info()))
    def add_failure(self):
        self._failures.append(Error(sys.exc_info()))
    def add_skip(self, reason):
        self._skips.append(reason)
    def get_errors(self):
        return self._errors
    def get_failures(self):
        return self._failures
    def get_skips(self):
        return self._skips
    def __repr__(self):
        return "< Result ({0})>".format(
            ", ".join(
                attr
                for attr in ("success", "error", "failure", "skip", "finished", "interrupted")
                if getattr(self, "is_{0}".format(attr))()
                )
            )

class GlobalResult(Result):
    pass

class SessionResult(object):
    def __init__(self, session_results_dict):
        super(SessionResult, self).__init__()
        self.global_result = GlobalResult()
        self._session_results_dict = session_results_dict
        self._iterator = functools.partial(itervalues, session_results_dict)
    def __iter__(self):
        return self._iterator()
    def is_success(self, allow_skips=False):
        return self.global_result.is_success() and \
            all(result.is_finished() and result.is_success(allow_skips=allow_skips)
                for result in self._iterator())
    def get_num_results(self):
        return len(self._session_results_dict)
    def get_num_successful(self):
        return self._count(Result.is_success_finished, include_global=False)
    def get_num_errors(self):
        return self._count(Result.is_error)
    def get_num_failures(self):
        return self._count(Result.is_just_failure)
    def get_num_skipped(self):
        return self._count(Result.is_skip)
    def _count(self, pred, include_global=True):
        returned = 0
        iterator = self.iter_all_results() if include_global else self.iter_test_results()
        for result in iterator:
            if pred(result):
                returned += 1
        return returned
    def iter_test_results(self):
        return iter(self)
    def iter_all_results(self):
        return itertools.chain(self.iter_test_results(), [self.global_result])
