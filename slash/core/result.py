import functools
import itertools
import os
import pickle
import sys
from numbers import Number

import gossip
import logbook
from vintage import deprecated

from .. import hooks
from .._compat import OrderedDict, itervalues
from ..ctx import context
from ..exception_handling import capture_sentry_exception, handling_exceptions
from .. import exceptions
from ..utils.exception_mark import ExceptionMarker
from ..utils.interactive import notify_if_slow_context
from ..utils.python import unpickle
from .details import Details
from .error import Error

_logger = logbook.Logger(__name__)

_ADDED_TO_RESULT = ExceptionMarker('added_to_result')


class Result(object):
    """Represents a single result for a test which was run
    """
    pickle_key_blacklist = {'test_metadata', 'facts'}

    def __init__(self, test_metadata=None):
        super(Result, self).__init__()
        self.test_metadata = test_metadata
        #: dictionary to be use by tests and plugins to store result-related information for later analysis
        self.data = {}
        self._errors = []
        self._failures = []
        self._skips = []
        #: a :class:`slash.core.details.Details` instance for storing additional test details
        self.details = Details()
        self.facts = Details(set_callback=self._fact_set_callback)
        self._started = False
        self._finished = False
        self._interrupted = False
        self._log_path = None
        self._extra_logs = []

    def _fact_set_callback(self, fact_name, fact_value):
        gossip.trigger('slash.fact_set', name=fact_name, value=fact_value)

    def is_global_result(self):
        return False

    def serialize(self):
        serialized_object = {}
        for key, value in vars(self).items():
            if key not in Result.pickle_key_blacklist:
                try:
                    serialized_object[key] = pickle.dumps(value)
                except (pickle.PicklingError, TypeError):
                    _logger.debug('Failed serializing result, skipping this value. key = {}', key)
                    capture_sentry_exception()
        return serialized_object

    def deserialize(self, result_dict):
        for key, value in result_dict.items():
            try:
                self.__dict__[key] = unpickle(value)
            except TypeError:
                _logger.error('Error when deserialize reult, skipping this value. key = {}', key,
                              extra={'capture': False})
        for failure in self._failures:
            self.add_failure(failure, append=False)
        for error in self._errors:
            self.add_error(error, append=False)
        for skip in self._skips:
            self.add_skip(skip, append=False)

    def add_exception(self, exc_info=None):
        """Adds the currently active exception, assuming it wasn't already added to a result
        """
        if exc_info is None:
            exc_info = sys.exc_info()
        _, exc_value, _ = exc_info  # pylint: disable=unpacking-non-sequence

        if _ADDED_TO_RESULT.is_exception_marked(exc_value):
            return

        _ADDED_TO_RESULT.mark_exception(exc_value)
        if isinstance(exc_value, exceptions.FAILURE_EXCEPTION_TYPES):
            self.add_failure()
        elif isinstance(exc_value, context.session.get_skip_exception_types()):
            self.add_skip(getattr(exc_value, 'reason', str(exc_value)))
        elif isinstance(exc_value, exceptions.INTERRUPTION_EXCEPTIONS):
            err = Error.capture_exception(exc_info=exc_info)
            hooks.interruption_added(result=self, exception=err) # pylint: disable=no-member
            session_result = context.session.results.global_result
            interrupted_test = self.is_interrupted()
            interrupted_session = session_result.is_interrupted()
            if not self.is_global_result():
                self.mark_interrupted()
                if not interrupted_test and not context.session.has_children():
                    with notify_if_slow_context(message="Cleaning up test due to interrupt. Please wait..."),\
                         handling_exceptions(swallow=True):

                        hooks.test_interrupt() # pylint: disable=no-member
            if not interrupted_session:
                session_result.mark_interrupted()

        elif not isinstance(exc_value, GeneratorExit):
            #skip keyboardinterrupt and system exit
            self.add_error(exc_info=exc_info)
        else:
            _logger.trace('Ignoring GeneratorExit exception')

    def has_errors_or_failures(self):
        return bool(self._failures or self._errors)

    def get_log_path(self):
        """Returns log path
        """
        return self._log_path

    def set_log_path(self, path):
        """Set log path
        """
        self._log_path = path

    def get_log_dir(self):
        """Returns log's directory.
        """
        if self._log_path is None:
            return None
        return os.path.dirname(self._log_path)

    def add_extra_log_path(self, path):
        """Add additional log path. This path will be added to the list returns by get_log_paths
        """
        self._extra_logs.append(path)

    def get_log_paths(self):
        """Returns a list of all log paths
        """
        logs = []
        if self._log_path:
            logs.append(self._log_path)
        return logs + list(self._extra_logs)

    def is_started(self):
        return self._started

    def is_not_run(self):
        return not self.is_started() and not self.has_errors_or_failures()

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

    def is_run_and_skip(self):
        return self.is_started() and self.is_skip()

    def is_success(self, allow_skips=False):
        if self._errors or self._failures or self._interrupted:
            return False
        if self._skips:
            return allow_skips
        return self.is_started()

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

    def add_error(self, e=None, frame_correction=0, exc_info=None, append=True):
        """Adds a failure to the result
        """
        err = self._add_error(self._errors, e, frame_correction=frame_correction + 1, exc_info=exc_info, append=append)
        context.reporter.report_test_error_added(context.test, err)
        return err

    def add_failure(self, e=None, frame_correction=0, exc_info=None, append=True):
        """Adds a failure to the result
        """
        err = self._add_error(self._failures, e, frame_correction=frame_correction + 1, exc_info=exc_info, is_failure=True, append=append)
        context.reporter.report_test_failure_added(context.test, err)
        return err

    def set_test_detail(self, key, value):
        """Adds a generic detail to this test result, which can be later inspected or used
        """
        self.details.set(key, value)

    def _add_error(self, error_list, error=None, frame_correction=0, exc_info=None, is_failure=False, append=True):
        try:
            if error is None:
                error = Error.capture_exception(exc_info=exc_info)
                if error is None:
                    raise RuntimeError('add_error() must be called with either an argument or in an active exception')
            if not isinstance(error, Error):
                error = Error(error, frame_correction=frame_correction + 1, exc_info=exc_info)
            if is_failure:
                # force the error object to be marked as failure
                error.mark_as_failure()
            error.log_added()
            if append:
                error_list.append(error)
            #report children errors or parent session errors only
            if not context.session or not context.session.has_children() or self.is_global_result():
                hooks.error_added(result=self, error=error)  # pylint: disable=no-member
            error.forget_exc_info()
            return error
        except Exception:
            _logger.error("Failed to add error to result", exc_info=True, extra={'capture': False})
            raise

    def add_skip(self, reason, append=True):
        if append:
            self._skips.append(reason)
        context.reporter.report_test_skip_added(context.test, reason)

    def get_errors(self):
        """Returns the list of errors recorded for this result

        :return: a list of :class:`slash.core.error.Error` objects
        """
        return self._errors

    def get_failures(self):
        """Returns the list of failures recorded for this result

        :return: a list of :class:`slash.core.error.Error` objects
        """
        return self._failures

    @deprecated('Use result.details.all()', since='0.20.0')
    def get_additional_details(self):
        return self.details.all()

    def get_skips(self):
        return self._skips

    def has_skips(self):
        return bool(self._skips)

    def has_fatal_errors(self):
        return any(e.is_fatal() for e in
                   itertools.chain(self._errors, self._failures))

    has_fatal_exception = has_fatal_errors

    def __repr__(self):
        return "<{} ({})>".format(
            self.__class__.__name__,
            ", ".join(
                attr
                for attr in ("success", "error", "failure", "skip", "finished", "interrupted")
                if getattr(self, "is_{}".format(attr))()
            )
        )


class GlobalResult(Result):

    def __init__(self, session_results=None):
        super(GlobalResult, self).__init__()
        self._session_results = session_results

    def is_global_result(self):
        return True

    def is_success(self, allow_skips=False):
        if not super(GlobalResult, self).is_success(allow_skips=allow_skips):
            return False
        if self._session_results is None:
            return True
        if self._session_results.session.has_children() and self._session_results.session.parallel_manager.server.worker_error_reported:
            return False
        return all(result.is_success(allow_skips=allow_skips) for result in self._session_results.iter_test_results())


class SessionResults(object):

    def __init__(self, session):
        super(SessionResults, self).__init__()
        self.session = session
        self.global_result = GlobalResult(self)
        self._results_dict = OrderedDict()
        self._iterator = functools.partial(itervalues, self._results_dict)

    def __len__(self):
        return len(self._results_dict)

    def __repr__(self):
        return '<Results: {} successful, {} errors, {} failures, {} skips>'.format(
            self.get_num_successful(),
            self.get_num_errors(),
            self.get_num_failures(),
            self.get_num_skipped())

    def iter_all_additional_details(self):
        for result in self.iter_all_results():
            if result.details:
                yield result, result.get_additional_details()

    def iter_all_failures(self):
        """Iterates over all results which have failures

        yields tuples of the form (result, failure_list)
        """
        for result in self.iter_all_results():
            if result.get_failures():
                yield result, result.get_failures()

    def iter_all_errors(self):
        """Iterates over all results which have errors

        yields tuples of the form (result, errors_list)
        """
        for result in self.iter_all_results():
            if result.get_errors():
                yield result, result.get_errors()

    @property
    def current(self):
        """Obtains the currently running result, if exists

        Otherwise, returns the global result object
        """
        return context.result

    def __iter__(self):
        return self._iterator()

    def is_success(self, allow_skips=False):
        """Indicates whether this run is successful

        :param allow_skips: Whether to consider skips as unsuccessful
        """
        return self.global_result.is_success(allow_skips=allow_skips)

    def is_interrupted(self):
        """Indicates if this session was interrupted
        """
        return any(result.is_interrupted() for result in self._iterator())

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

    def get_num_skipped(self, include_not_run=True):
        if include_not_run:
            return self._count(Result.is_skip)
        return self._count(Result.is_run_and_skip)

    def get_num_not_run(self):
        return self._count(Result.is_not_run, include_global=False)

    def has_fatal_errors(self):
        """Indicates whether any result has an error marked as fatal (causing the session to terminate)
        """
        return bool(self._count(Result.has_fatal_errors))

    def _count(self, pred, include_global=True):
        returned = 0
        iterator = self.iter_all_results(
        ) if include_global else self.iter_test_results()
        for result in iterator:
            if pred(result):
                returned += 1
        return returned

    def iter_test_results(self):
        """Iterates over results belonging to tests
        """
        return iter(self)

    def iter_all_results(self):
        """Iterates over all results, ending with the global result object
        """
        return itertools.chain(self.iter_test_results(), [self.global_result])

    def create_result(self, test):
        if test.__slash__.id in self._results_dict:
            raise exceptions.SlashInternalError("{} shouldn't appear in results dict before adding its result".format(test.__slash__.id))

        returned = Result(test.__slash__)
        self._results_dict[test.__slash__.id] = returned
        return returned

    def get_result(self, test):
        """Returns the result stored belonging to a given test
        """
        if test.__slash__ is None:
            raise LookupError("Could not find result for {}".format(test))
        return self._results_dict[test.__slash__.id]

    def __getitem__(self, test):
        if isinstance(test, Number):
            try:
                return next(itertools.islice(itervalues(self._results_dict), test, test + 1))
            except StopIteration:
                raise IndexError()
        return self.get_result(test)
