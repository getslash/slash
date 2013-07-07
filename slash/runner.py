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
from .exception_handling import handling_exceptions
from .metadata import ensure_slash_metadata
from .test_context import get_test_context_setup
from .utils.peekable_iterator import PeekableIterator
from contextlib import contextmanager
import logbook # pylint: disable=F0401

_logger = logbook.Logger(__name__)

def run_tests(iterable):
    """
    Runs tests from an iterable using the current session
    """
    test_iterator = PeekableIterator(iterable)
    for test in test_iterator:
        ensure_slash_metadata(test).id = context.session.id_space.allocate()
        _logger.debug("Running {0}...", test)
        with _get_test_context(test):
            with _get_test_hooks_context():
                with _update_result_context() as result:
                    try:
                        with handling_exceptions():
                            with get_test_context_setup(test, test_iterator.peek_or_none()):
                                test.run()
                    finally:
                        call_cleanups()
        if not result.is_success() and not result.is_skip() and config.root.run.stop_on_error:
            _logger.debug("Stopping (run.stop_on_error==True)")
            break
    else:
        context.session.mark_complete()

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
    except TestFailed:
        hooks.test_failure()
    except KeyboardInterrupt:
        hooks.test_interrupt()
        raise
    except:
        hooks.test_error()
    else:
        hooks.test_success()
    finally:
        hooks.test_end()

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
    result = context.session.create_result(context.test)
    try:
        try:
            yield result
        except:
            _logger.debug("Exception escaped test", exc_info=sys.exc_info())
            raise
    except SkipTest as e:
        result.add_skip(e.reason)
        raise
    except TestFailed:
        result.add_failure()
        raise
    except:
        result.add_error()
        raise
    finally:
        result.mark_finished()
