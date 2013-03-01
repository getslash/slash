from .ctx import context
from .exceptions import TestFailed
from .metadata import ensure_shakedown_metadata
from contextlib import contextmanager
import logbook # pylint: disable=F0401

_logger = logbook.Logger(__name__)

def run_tests(iterable):
    """
    Runs tests from an iterable using the current suite
    """
    for test in iterable:
        _logger.debug("Running {0}...", test)
        ensure_shakedown_metadata(test).id = context.suite.id_space.allocate()
        with _set_current_test_context(test):
            with _report_result_context():
                test.run()

@contextmanager
def _set_current_test_context(test):
    prev = context.test
    context.test = test
    try:
        yield
    finally:
        context.test = prev

@contextmanager
def _report_result_context():
    result = context.suite.create_result(context.test)
    try:
        try:
            yield
        except:
            _logger.exception("Exception escaped test")
            raise
    except TestFailed as e:
        result.add_failure(e)
    except Exception as e: # pylint: disable=W0702
        result.add_error(e)
    finally:
        result.mark_finished()
