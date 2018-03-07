# pylint: disable=redefined-outer-name
import pytest
import slash.resuming
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

def test_delete_old_sessions(suite):
    result = suite.run()
    assert result.session.id == get_last_resumeable_session_id()
    slash.resuming._MAX_DAYS_SAVED_SESSIONS = 0 # pylint: disable=protected-access
    result = suite.run()
    with pytest.raises(CannotResume):
        get_last_resumeable_session_id()
