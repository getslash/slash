import sys
from contextlib import contextmanager

import logbook

from . import hooks
from ._compat import ExitStack
from .cleanups import call_cleanups
from .conf import config
from .ctx import context
from .exception_handling import handling_exceptions
from .exceptions import NoActiveSession, SkipTest, TestFailed
from .metadata import ensure_test_metadata
from .test_context import get_test_context_setup
from .utils.iteration import PeekableIterator
from .core.error import Error, DetailedTraceback

_logger = logbook.Logger(__name__)

def run_tests(iterable, stop_on_error=None):
    """
    Runs tests from an iterable using the current session
    """
    #pylint: disable=maybe-no-member
    if context.session is None:
        raise NoActiveSession("A session is not currently active")

    if stop_on_error is None:
        stop_on_error = config.root.run.stop_on_error

    test_iterator = PeekableIterator(iterable)
    last_filename = None
    complete = False
    for test in test_iterator:
        ensure_test_metadata(test)
        test_filename = test.__slash__.fqn.path
        if last_filename != test_filename:
            context.session.reporter.report_file_start(test_filename)
            last_filename = test_filename
        context.session.reporter.report_test_start(test)
        _logger.debug("Running {0}...", test)
        with _get_run_context_stack(test, test_iterator):
            test.run()
        result = context.session.results[test]
        context.session.reporter.report_test_end(test, result)
        if not test_iterator.has_next() or ensure_test_metadata(test_iterator.peek()).fqn.path != last_filename:
            context.session.reporter.report_file_end(last_filename)
        if result.has_fatal_exception():
            _logger.debug("Stopping on fatal exception")
            break
        if not result.is_success() and not result.is_skip() and stop_on_error:
            _logger.debug("Stopping (run.stop_on_error==True)")
            break
    else:
        complete = True

    _mark_remaining_skipped(test_iterator)
    if complete:
        context.session.mark_complete()
    elif last_filename is not None:
        context.session.reporter.report_file_end(last_filename)

def _mark_remaining_skipped(test_iterator):
    for test in test_iterator:
        with _get_test_context(test):
            context.session.results.create_result(test).add_skip("Did not run")

@contextmanager
def _get_run_context_stack(test, test_iterator):
    yielded = False
    with ExitStack() as stack:
        stack.enter_context(_get_test_context(test))
        stack.enter_context(_get_test_hooks_context())
        stack.enter_context(_update_result_context())
        stack.enter_context(_cleanup_context())
        stack.enter_context(handling_exceptions())
        stack.enter_context(get_test_context_setup(test, test_iterator.peek_or_none()))
        yielded = True
        yield
    # if some of the context entries throw SkipTest, the yield result above will not be reached.
    # we have to make sure that yield happens or else the context manager will raise on __exit__...
    if not yielded:
        yield

@contextmanager
def _cleanup_context():
    # In Python 2.6, exc_info() in finally is sometimes (None, None, None), so we capture it explicitly
    exc_info = None
    try:
        try:
            yield
        except:
            exc_info = sys.exc_info()
            raise
    finally:
        call_cleanups(critical_only=exc_info is not None and exc_info[0] is KeyboardInterrupt)
        del exc_info

@contextmanager
def _get_test_context(test):
    ensure_test_metadata(test)
    assert test.__slash__.id is None
    test.__slash__.id = context.session.id_space.allocate()

    with _set_current_test_context(test):
        with context.session.logging.get_test_logging_context():
            yield

@contextmanager
def _get_test_hooks_context():
    hooks.test_start()  # pylint: disable=no-member
    try:
        yield
    except SkipTest as skip_exception:
        hooks.test_skip(reason=skip_exception.reason)  # pylint: disable=no-member
    except TestFailed:
        hooks.test_failure()  # pylint: disable=no-member
    except KeyboardInterrupt:
        hooks.test_interrupt()  # pylint: disable=no-member
        raise
    except:
        hooks.test_error()  # pylint: disable=no-member
    else:
        if context.session.results.get_result(context.test).is_success_finished():
            hooks.test_success()  # pylint: disable=no-member
        else:
            hooks.test_error()  # pylint: disable=no-member
    finally:
        hooks.test_end()  # pylint: disable=no-member

@contextmanager
def _set_current_test_context(test):
    prev_test = context.test
    prev_test_id = context.test_id
    context.test = test
    context.test_id = test.__slash__.id
    try:
        yield
    finally:
        context.test = prev_test
        context.test_id = prev_test_id

@contextmanager
def _update_result_context():
    result = context.session.results.create_result(context.test)
    result.set_log_path(context.session.logging.test_log_path)
    result.mark_started()
    try:
        try:
            yield result
        except:
            _logger.debug("Exception escaped test:\n{0}", DetailedTraceback(Error.capture_exception()))
            raise
    except SkipTest as e:
        result.add_skip(e.reason)
        raise
    except KeyboardInterrupt:
        result.mark_interrupted()
        raise
    finally:
        result.mark_finished()
