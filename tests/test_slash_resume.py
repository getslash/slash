# pylint: disable=redefined-outer-name
import pytest
from slash.resuming import (CannotResume, get_last_resumeable_session_id, get_tests_from_previous_session)


def test_resume_no_session():
    with pytest.raises(CannotResume):
        get_tests_from_previous_session("nonexisting_session")

def test_get_last_resumeable_session(suite):
    suite[len(suite) // 2].when_run.fail()
    prev_id = None
    for i in range(5):  # pylint: disable=unused-variable
        results = suite.run()
        assert results.session.id != prev_id
        prev_id = results.session.id
        assert get_last_resumeable_session_id() == results.session.id

def test_resume(suite):
    fail_index = len(suite) // 2
    suite[fail_index].when_run.fail()
    for index, test in enumerate(suite):
        if index > fail_index:
            test.expect_not_run()
    result = suite.run(additional_args=['-x'])
    resumed = get_tests_from_previous_session(result.session.id)

    assert len(resumed) + result.session.results.get_num_started() - 1 == len(suite)

def test_resume_with_parametrization(suite, suite_test):
    num_values1 = 3
    num_values2 = 5
    suite_test.add_parameter(num_values=num_values1)
    suite_test.add_parameter(num_values=num_values2)
    fail_index = len(suite) // 2
    suite[fail_index].when_run.fail()
    summary = suite.run()
    resumed = get_tests_from_previous_session(summary.session.id)

    assert len(summary.get_all_results_for_test(suite_test)) == num_values1 * num_values2
    assert len(resumed) == 1
    assert resumed[0].function_name == suite[fail_index].name

def test_different_folder_no_resume_session_id(suite, tmpdir):  # pylint: disable=unused-argument
    fail_index = len(suite) // 2
    suite[fail_index].when_run.fail()
    suite.run()
    sessoin_id = get_last_resumeable_session_id()

    assert sessoin_id
    with tmpdir.ensure_dir().as_cwd():
        with pytest.raises(CannotResume):
            sessoin_id = get_last_resumeable_session_id()

def test_delete_old_sessions(suite, config_override):
    result = suite.run()
    assert result.session.id == get_last_resumeable_session_id()
    config_override('resume.state_retention_days', 0)
    result = suite.run()
    with pytest.raises(CannotResume):
        get_last_resumeable_session_id()

def test_failed_and_unstarted_first_fails(suite, config_override):
    config_override('resume.failed_first', True)
    config_override('resume.unstarted_first', True)
    result = suite.run()
    with pytest.raises(CannotResume):
        get_tests_from_previous_session(result.session.id)

@pytest.mark.parametrize('failed_first', [True, False])
def test_failed_first_or_unstarted_first(suite, failed_first, config_override):
    fail_index = len(suite) // 2
    skip_index = fail_index - 1
    suite[skip_index].when_run.skip()
    suite[fail_index].when_run.fail()
    for index, test in enumerate(suite):
        if index > fail_index:
            test.expect_not_run()
    result = suite.run(additional_args=['-x'])
    regular_order = get_tests_from_previous_session(result.session.id)
    if failed_first:
        config_override('resume.failed_first', True)
    else:
        config_override('resume.unstarted_first', True)

    order_after_changing_config = get_tests_from_previous_session(result.session.id)
    assert len(order_after_changing_config) + result.session.results.get_num_started() - 2 == len(suite)

    first_test_in_resumed_suite = fail_index if failed_first else skip_index
    assert order_after_changing_config[0].function_name == suite[first_test_in_resumed_suite].name

    if failed_first:
        assert regular_order[1] == order_after_changing_config[0]
        assert regular_order[0] == order_after_changing_config[1]
        assert regular_order[2:] == order_after_changing_config[2:]
    else:
        failed_test = order_after_changing_config.pop(len(order_after_changing_config)-1)
        order_after_changing_config.insert(1, failed_test)
        assert regular_order == order_after_changing_config

@pytest.mark.parametrize('failed_first', [True, False])
def test_failed_or_unstarted_with_no_such_tests(suite, failed_first, suite_test, config_override):
    if failed_first:
        suite_test.when_run.skip()
    else:
        suite_test.when_run.fail()
    result = suite.run()
    if failed_first:
        config_override('resume.failed_first', True)
    else:
        config_override('resume.unstarted_first', True)
    [resumed_test] = get_tests_from_previous_session(result.session.id)
    assert resumed_test.function_name == suite_test.name

@pytest.mark.parametrize('failed_only', [True, False])
def test_failed_only_or_unstarted_first(suite, failed_only, config_override):
    fail_index = len(suite) // 2
    skip_index = fail_index - 1
    suite[skip_index].when_run.skip()
    suite[fail_index].when_run.fail()
    for index, test in enumerate(suite):
        if index > fail_index:
            test.expect_not_run()
    result = suite.run(additional_args=['-x'])

    if failed_only:
        config_override('resume.failed_only', True)
        expected_resume_tests_num = 1
        expected_status = 'failed'
    else:
        config_override('resume.unstarted_only', True)
        expected_resume_tests_num = len(suite) - fail_index
        expected_status = 'planned'
    resumed = get_tests_from_previous_session(result.session.id)

    assert len(resumed) == expected_resume_tests_num
    for test in resumed:
        assert test.status == expected_status
