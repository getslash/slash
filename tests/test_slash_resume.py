# pylint: disable=redefined-outer-name
import os
import pytest
from tempfile import mkdtemp
from slash.resuming import (CannotResume, get_last_resumeable_session_id, get_tests_to_resume)

@pytest.fixture()
def set_resume_cwd(request):
    prev = os.getcwd()

    @request.addfinalizer
    def cleanup():
        os.chdir(prev)

def test_resume_no_session():
    with pytest.raises(CannotResume):
        get_tests_to_resume("nonexisting_session")

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
    resumed = get_tests_to_resume(result.session.id)

    assert len(resumed) + result.session.results.get_num_started() - 1 == len(suite)

def test_resume_with_parametrization(suite):
    num_values1 = 3
    num_values2 = 5
    test = suite.add_test(type='method')
    test.add_parameter(num_values=num_values1)
    test.add_parameter(num_values=num_values2)
    fail_index = len(suite) // 2
    suite[fail_index].when_run.fail()
    summary = suite.run()

    assert len(summary.get_all_results_for_test(test)) == num_values1 * num_values2
    resumed = get_tests_to_resume(summary.session.id)
    assert len(resumed) == 1

def test_different_folder_no_resume_session_id(suite, set_resume_cwd):
    fail_index = len(suite) // 2
    suite[fail_index].when_run.fail()
    suite.run()
    sessoin_id = get_last_resumeable_session_id()
    assert sessoin_id

    os.chdir(os.path.dirname(mkdtemp()))
    with pytest.raises(CannotResume):
        sessoin_id = get_last_resumeable_session_id()
