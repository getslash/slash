from .ctx import ctx
from .exceptions import TestFailed
from .metadata import ensure_shakedown_metadata
from contextlib import contextmanager

def run_tests(iterable):
    """
    Runs tests from an iterable using the current suite
    """
    for test in iterable:
        ensure_shakedown_metadata(test).id = ctx.suite.id_space.allocate()
        with _set_current_test_context(test):
            with _report_result_context():
                test.run()

@contextmanager
def _set_current_test_context(test):
    prev = ctx.test
    ctx.test = test
    try:
        yield
    finally:
        ctx.test = prev

@contextmanager
def _report_result_context():
    result = ctx.session.create_result(ctx.test)
    try:
        yield
    except TestFailed as e:
        result.add_failure(e)
    except Exception as e: # pylint: disable=W0702
        result.add_error(e)
    finally:
        result.mark_finished()
