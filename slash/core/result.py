import functools
import itertools

import logbook

from .._compat import itervalues, OrderedDict
from ..ctx import context
from .error import Error

_logger = logbook.Logger(__name__)

class Result(object):

    def __init__(self, test_metadata=None):
        super(Result, self).__init__()
        self.test_metadata = test_metadata
        #: dictionary to be use by tests and plugins to store result-related information for later analysis
        self.data = {}
        self._errors = []
        self._failures = []
        self._skips = []
        self._started = False
        self._finished = False
        self._interrupted = False
        self._log_path = None

    def get_log_path(self):
        return self._log_path

    def set_log_path(self, path):
        self._log_path = path

    def is_started(self):
        return self._started

    def mark_started(self):
        self._started = True

    def is_error(self):
        return bool(self._errors)

    @property
    def test_id(self):
        return self.test_metadata.id

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

    def add_error(self, e=None):
        self._add_error(self._errors, e)

    def add_failure(self, e=None):
        self._add_error(self._failures, e)

    def _add_error(self, error_list, error=None):
        try:
            if error is None:
                error = Error.capture_exception()
            if not isinstance(error, Error):
                error = Error(error)
            error_list.append(error)
        except Exception:
            _logger.error("Failed to add error to result", exc_info=True)
            raise

    def add_skip(self, reason):
        self._skips.append(reason)

    def get_errors(self):
        return self._errors

    def get_failures(self):
        return self._failures

    def get_skips(self):
        return self._skips

    def has_fatal_exception(self):
        return any(e.is_fatal() for e in
            itertools.chain(self._errors, self._failures))

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


class SessionResults(object):

    def __init__(self, session):
        super(SessionResults, self).__init__()
        self.session = session
        self.global_result = GlobalResult()
        self._results_dict = OrderedDict()
        self._iterator = functools.partial(itervalues, self._results_dict)

    def __len__(self):
        return len(self._results_dict)

    def iter_all_failures(self):
        for result in self.iter_all_results():
            if result.get_failures():
                yield result, result.get_failures()

    def iter_all_errors(self):
        for result in self.iter_all_results():
            if result.get_errors():
                yield result, result.get_errors()

    @property
    def current(self):
        test_id = context.test_id
        if test_id is None:
            return self.global_result
        return self._results_dict[test_id]

    def __iter__(self):
        return self._iterator()

    def is_success(self, allow_skips=False):
        return self.global_result.is_success() and \
            all(result.is_finished() and result.is_success(allow_skips=allow_skips)
                for result in self._iterator())

    def get_num_results(self):
        return len(self._results_dict)

    def get_num_started(self):
        return self._count(Result.is_started, include_global=False)

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
        iterator = self.iter_all_results(
        ) if include_global else self.iter_test_results()
        for result in iterator:
            if pred(result):
                returned += 1
        return returned

    def iter_test_results(self):
        return iter(self)

    def iter_all_results(self):
        return itertools.chain(self.iter_test_results(), [self.global_result])

    def create_result(self, test):
        assert test.__slash__.id not in self._results_dict
        returned = Result(test.__slash__)
        self._results_dict[test.__slash__.id] = returned
        return returned

    def get_result(self, test):
        if test.__slash__ is None:
            raise LookupError("Could not find result for {0}".format(test))
        return self._results_dict[test.__slash__.id]

    def __getitem__(self, test):
        return self.get_result(test)
