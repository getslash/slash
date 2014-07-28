# pylint: disable-msg=W0201
import functools

import pytest
import slash
from slash.exceptions import NoActiveSession
from slash.runner import run_tests


def test_run_tests_fails_without_active_session():
    with pytest.raises(NoActiveSession):
        run_tests([])


def test_simple_run(populated_suite):
    populated_suite.run()


def test_iter_results_ordering(populated_suite):
    for index, test in enumerate(populated_suite):
        test.inject_line('slash.context.result.data["index"] = {0}'.format(index))

    results = list(populated_suite.run().session.results.iter_test_results())

    for index, result in enumerate(results):
        assert result.data['index'] == index


def test_failed(populated_suite, test):
    test.fail()
    result = populated_suite.run()[test]
    assert result.is_failure()
    assert not result.is_error()
    assert not result.is_success()


def test_error(populated_suite, test):
    test.error()
    result = populated_suite.run()[test]
    assert result.is_error()
    assert not result.is_failure()
    assert not result.is_success()


def test_skip(populated_suite, test):
    test.skip()
    result = populated_suite.run()[test]
    assert result.is_skip()
    assert not result.is_error()
    assert not result.is_failure()
    assert not result.is_success()


@pytest.mark.parametrize('failure_type', ['failure', 'error'])
def test_stop_on_fatal_exception(populated_suite, test, remaining_tests, failure_type):
    test.inject_line(
        'from slash.exception_handling import mark_exception_fatal')
    test.inject_line('raise mark_exception_fatal({0}())'.format('AssertionError' if failure_type == 'failure' else 'Exception'))
    getattr(test, 'expect_{0}'.format(failure_type))()
    for remaining_test in remaining_tests:
        remaining_test.expect_skip()

    populated_suite.run()


@pytest.mark.parametrize('failure_type', ['error', 'failure'])
def test_stop_on_error(populated_suite, test, failure_type):
    if failure_type == 'error':
        test.error()
    elif failure_type == 'failure':
        test.fail()
    else:
        raise NotImplementedError()  # pragma: no cover

    populated_suite.run(stop_on_error=True)


def test_stop_on_error_unaffected_by_skips(populated_suite, test):
    assert test is not populated_suite[-1]
    test.skip()
    results = populated_suite.run(stop_on_error=True)
    assert results[populated_suite[-1]].is_success()


def test_debug_if_needed(request, config_override, populated_suite, test):
    test.fail()

    debugged = {'value': False}

    def _debug_if_needed(exc_info):
        debugged['value'] = True

    request.addfinalizer(functools.partial(
        setattr, slash.utils.debug, '_KNOWN_DEBUGGERS', slash.utils.debug._KNOWN_DEBUGGERS))
    slash.utils.debug._KNOWN_DEBUGGERS = [_debug_if_needed]

    config_override('run.stop_on_error', True)
    config_override('debug.enabled', True)

    populated_suite.run()

    assert debugged['value']


@pytest.fixture
def test(populated_suite, test_index):
    return populated_suite[test_index]


@pytest.fixture
def test_index(populated_suite):
    return int(len(populated_suite) // 2)


@pytest.fixture
def remaining_tests(populated_suite, test_index):
    return populated_suite[test_index + 1:]
