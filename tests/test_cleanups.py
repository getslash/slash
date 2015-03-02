import pytest
import gossip
import slash
import slash.runner
from slash import exception_handling, Session
from slash.loader import Loader

from .utils import TestCase


def test_test_cleanups_happen_before_fixture_cleanups(suite, suite_test):
    fixture = suite.slashconf.add_fixture()
    suite_test.depend_on_fixture(fixture)
    fixture_cleanup = fixture.add_cleanup()
    test_cleanup = suite_test.add_cleanup()
    events = suite.run().events

    assert events[fixture_cleanup].timestamp > events[test_cleanup].timestamp


def test_cannot_add_cleanup_without_active_session():
    with pytest.raises(RuntimeError):
        slash.add_cleanup(lambda: None)


def test_cleanups(suite, suite_test):

    cleanup = suite_test.add_cleanup()

    summary = suite.run()

    assert summary.events[cleanup]


def test_cleanup_args_kwargs_deprecated():
    with slash.Session() as s:
        slash.add_cleanup(lambda: None, "arg1", arg2=1)
    [w] = s.warnings
    assert 'deprecated' in str(w).lower()


def test_cleanup_ordering(suite, suite_test):
    cleanup1 = suite_test.add_cleanup()
    cleanup2 = suite_test.add_cleanup()
    events = suite.run().events

    assert events[cleanup1].timestamp > events[cleanup2].timestamp


@pytest.mark.parametrize('fail_test', [True, False])
def test_errors_in_cleanup(suite, suite_test, fail_test):
    cleanup1 = suite_test.add_cleanup()
    cleanup2 = suite_test.add_cleanup(extra_code=['None.a = 2'])

    if fail_test:
        suite_test.when_run.raise_exception()
    else:
        suite_test.expect_error()

    summary = suite.run()

    assert summary.events[cleanup1].timestamp > summary.events[cleanup2].timestamp

    [result] = summary.get_all_results_for_test(suite_test)

    assert len(result.get_errors()) == 2 if fail_test else 1
    cleanup_error = result.get_errors()[-1]
    assert 'AttributeError' in str(cleanup_error)
    assert 'NoneType' in str(cleanup_error)

