# pylint: disable-msg=W0201
import functools

import pytest
import slash
from slash.exceptions import NoActiveSession
from slash.runner import run_tests


def test_run_tests_fails_without_active_session():
    with pytest.raises(NoActiveSession):
        run_tests([])


def test_simple_run(suite):
    suite.run()


def test_iter_results_ordering(suite):
    for index, test in enumerate(suite):
        test.append_line('slash.context.result.data["index"] = {0}'.format(index))

    results = list(suite.run().session.results.iter_test_results())

    for index, result in enumerate(results):
        assert result.data['index'] == index


def test_failed(suite, test):
    test.when_run.fail()
    result = suite.run()[test]
    assert result.is_failure()
    assert not result.is_error()
    assert not result.is_success()


def test_error(suite, test):
    test.when_run.error()
    result = suite.run()[test]
    assert result.is_error()
    assert not result.is_failure()
    assert not result.is_success()


def test_skip(suite, test):
    test.when_run.skip()
    result = suite.run()[test]
    assert result.is_skip()
    assert not result.is_error()
    assert not result.is_failure()
    assert not result.is_success()


@pytest.mark.parametrize('failure_type', ['failure', 'error'])
def test_stop_on_fatal_exception(suite, test, remaining_tests, failure_type):
    test.append_line(
        'from slash.exception_handling import mark_exception_fatal')
    test.append_line('raise mark_exception_fatal({0}())'.format('AssertionError' if failure_type == 'failure' else 'Exception'))
    getattr(test, 'expect_{0}'.format(failure_type))()
    for remaining_test in remaining_tests:
        remaining_test.expect_not_run()

    suite.run()


@pytest.mark.parametrize('failure_type', ['error', 'failure'])
def test_stop_on_error(suite, test, test_index, failure_type):
    if failure_type == 'error':
        test.when_run.error()
    elif failure_type == 'failure':
        test.when_run.fail()
    else:
        raise NotImplementedError()  # pragma: no cover

    for index, test in enumerate(suite):
        if index > test_index:
            test.expect_not_run()

    suite.run(additional_args=['-x'])


def test_stop_on_error_unaffected_by_skips(suite, test):
    assert test is not suite[-1]
    test.when_run.skip()
    results = suite.run(additional_args=['-x'])
    assert results[suite[-1]].is_success()


def test_debug_if_needed(request, config_override, suite, test):
    test.when_run.fail()

    debugged = {'value': False}

    def _debug_if_needed(exc_info):
        debugged['value'] = True

    request.addfinalizer(functools.partial(
        setattr, slash.utils.debug, '_KNOWN_DEBUGGERS', slash.utils.debug._KNOWN_DEBUGGERS))
    slash.utils.debug._KNOWN_DEBUGGERS = [_debug_if_needed]

    config_override('debug.enabled', True)

    suite.run()

    assert debugged['value']


@pytest.fixture
def test(suite, test_index):
    return suite[test_index]


@pytest.fixture
def test_index(suite):
    return int(len(suite) // 2)


@pytest.fixture
def remaining_tests(suite, test_index):
    return suite[test_index + 1:]
