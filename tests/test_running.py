# pylint: disable-msg=W0201
import functools

import pytest
import slash
from slash.exceptions import NoActiveSession
from slash.runner import run_tests


@pytest.mark.parametrize('adder', ['add_failure', 'add_error'])
def test_stop_on_error_with_error_and_skip(suite, adder):
    suite_test = suite[2]
    suite_test.append_line('slash.{0}("err")'.format(adder))
    suite_test.append_line('slash.skip_test()')
    suite_test.expect_skip()

    for test in suite.iter_all_after(suite_test, assert_has_more=True):
        test.expect_not_run()

    summary = suite.run(additional_args=['-x'])
    [result] = summary.get_all_results_for_test(suite_test)

    assert result.has_skips()
    assert result.has_errors_or_failures()


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


def test_failed(suite, suite_test):
    suite_test.when_run.fail()
    result = suite.run()[suite_test]
    assert result.is_failure()
    assert not result.is_error()
    assert not result.is_success()


def test_error(suite, suite_test):
    suite_test.when_run.error()
    result = suite.run()[suite_test]
    assert result.is_error()
    assert not result.is_failure()
    assert not result.is_success()


def test_skip(suite, suite_test):
    suite_test.when_run.skip()
    result = suite.run()[suite_test]
    assert result.is_skip()
    assert not result.is_error()
    assert not result.is_failure()
    assert not result.is_success()


def test_stop_on_fatal_exception(suite, suite_test, fatal_error_adder):
    fatal_error_adder(suite_test)
    for remaining_test in suite.iter_all_after(suite_test):
        remaining_test.expect_not_run()

    suite.run()


def test_stop_on_error(suite, suite_test, failure_type):
    if failure_type == 'error':
        suite_test.when_run.error()
    elif failure_type == 'failure':
        suite_test.when_run.fail()
    else:
        raise NotImplementedError()  # pragma: no cover

    for test in suite.iter_all_after(suite_test):
        test.expect_not_run()

    suite.run(additional_args=['-x'])


def test_stop_on_error_unaffected_by_skips(suite, suite_test):
    suite_test.when_run.skip()
    summary = suite.run(additional_args=['-x'])
    for test in suite.iter_all_after(suite_test):
        for res in summary.get_all_results_for_test(test):
            assert res.is_success()



def test_debug_if_needed(request, config_override, suite, suite_test):
    suite_test.when_run.fail()

    debugged = {'value': False}

    def _debug_if_needed(exc_info):
        debugged['value'] = True

    request.addfinalizer(functools.partial(
        setattr, slash.utils.debug, '_KNOWN_DEBUGGERS', slash.utils.debug._KNOWN_DEBUGGERS))
    slash.utils.debug._KNOWN_DEBUGGERS = [_debug_if_needed]

    config_override('debug.enabled', True)

    suite.run()

    assert debugged['value']

@pytest.fixture(params=['raising', 'adding'])
def fatal_error_adder(request, failure_type):

    def adder(test):
        if request.param == 'raising':
            test.append_line(
                'from slash.exception_handling import mark_exception_fatal')
            test.append_line('raise mark_exception_fatal({0}())'.format('AssertionError' if failure_type == 'failure' else 'Exception'))
        elif request.param == 'adding':
            test.append_line('slash.add_{0}("msg").mark_fatal()'.format(failure_type))
        else:
            raise NotImplementedError() # pragma: no cover

        getattr(test, 'expect_{0}'.format(failure_type))()
    return adder


@pytest.fixture(params=['failure', 'error'])
def failure_type(request):
    return request.param
