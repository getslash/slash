# pylint: disable=attribute-defined-outside-init,redefined-outer-name
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


@pytest.mark.parametrize('adder', ['add_failure', 'add_error'])
def test_stop_on_error_from_previous_run(suite, adder):
    test_a = suite[2]
    test_b = suite[4]

    # avoid slash.ctx here, because the stored object would be a proxy
    test_a.append_line('slash.g.inject_to_result = slash.context.session.results.current')
    test_b.append_line('slash.g.inject_to_result.{}("injected")'.format(adder))

    if adder == 'add_error':
        test_a.expect_error()
    elif adder == 'add_failure':
        test_a.expect_failure()
    else:
        raise NotImplementedError() # pragma: no cover

    all_after = list(suite.iter_all_after(test_b))
    assert all_after
    for test in all_after:
        test.expect_not_run()

    suite.run(additional_args=['-x'])


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


@pytest.mark.parametrize('stop_through_config', [True, False])
def test_stop_on_error(suite, suite_test, failure_type, stop_through_config, config_override):
    if failure_type == 'error':
        suite_test.when_run.error()
    elif failure_type == 'failure':
        suite_test.when_run.fail()
    else:
        raise NotImplementedError()  # pragma: no cover

    for test in suite.iter_all_after(suite_test):
        test.expect_not_run()

    if stop_through_config:
        config_override('run.stop_on_error', True)
        kwargs = {}
    else:
        config_override('run.stop_on_error', False)
        kwargs = {'additional_args': ['-x']}
    suite.run(**kwargs)


def test_stop_on_error_unaffected_by_skips(suite, suite_test):
    suite_test.when_run.skip()
    summary = suite.run(additional_args=['-x'])
    for test in suite.iter_all_after(suite_test):
        for res in summary.get_all_results_for_test(test):
            assert res.is_success()



def test_debug_if_needed(request, config_override, suite, suite_test):
    suite_test.when_run.fail()

    debugged = {'value': False}

    def _debug_if_needed(exc_info):  # pylint: disable=unused-argument
        debugged['value'] = True

    # pylint: disable=protected-access
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
