import sys
from . import log
from . import hooks
from .cleanups import call_cleanups
from .conf import config
from .ctx import context
from .exceptions import (
    TestFailed,
    SkipTest,
    )
from .metadata import ensure_shakedown_metadata
from .exception_handling import handling_exceptions
from contextlib import contextmanager
import logbook # pylint: disable=F0401

_logger = logbook.Logger(__name__)

def run_tests(iterable):
    """
    Runs tests from an iterable using the current suite
    """
    for test in iterable:
        ensure_shakedown_metadata(test).id = context.suite.id_space.allocate()
        _logger.debug("Running {0}...", test)
        with _get_test_context(test):
            with _update_result_context() as result:
                with _get_test_hooks_context():
                    try:
                        with handling_exceptions():
                            test.run()
                    finally:
                        call_cleanups()
        if not result.is_success() and not result.is_skip() and config.root.run.stop_on_error:
            _logger.debug("Stopping (run.stop_on_error==True)")
            context.suite.mark_incomplete()
            break

@contextmanager
def _get_test_context(test):
    with _set_current_test_context(test):
        with log.get_test_logging_context():
            yield

@contextmanager
def _get_test_hooks_context():
    hooks.test_start()
    try:
        yield
    except SkipTest:
        hooks.test_skip()
        raise
    except TestFailed:
        hooks.test_failure()
        raise
    except:
        hooks.test_error()
        raise
    finally:
        hooks.test_end()

@contextmanager
def _set_current_test_context(test):
    prev_test = context.test
    prev_test_id = context.test_id
    context.test = test
    context.test_id = test.__shakedown__.id
    try:
        yield
    finally:
        context.test = prev_test
        context.test_id = prev_test_id

@contextmanager
def _update_result_context():
    result = context.suite.create_result(context.test)
    try:
        try:
            yield result
        except:
            _logger.debug("Exception escaped test", exc_info=sys.exc_info())
            raise
    except SkipTest as e:
        result.add_skip(e.reason)
    except TestFailed:
        result.add_failure()
    except:
        result.add_error()
    finally:
        result.mark_finished()
