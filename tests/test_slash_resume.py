import os
import time

import pytest
from slash import resuming
from slash.resuming import (_MAX_NUM_SAVED_SESSIONS, CannotResume, get_last_resumeable_session_id,
                            get_tests_to_resume, save_resume_state)


def test_resume_no_session():
    with pytest.raises(CannotResume):
        get_tests_to_resume("nonexisting_session")

def test_max_resumed_sessions(populated_suite):
    for i in range(1, _MAX_NUM_SAVED_SESSIONS + 2):
        results = populated_suite.run()
        save_resume_state(results.session.results)
        assert len(os.listdir(resuming._RESUME_DIR)) == min(_MAX_NUM_SAVED_SESSIONS, i)

def test_get_last_resumeable_session(populated_suite):
    populated_suite.fail_in_middle()
    prev_id = None
    for i in range(5):
        results = populated_suite.run()
        assert results.session.id != prev_id
        prev_id = results.session.id
        save_resume_state(results.session.results)
        assert get_last_resumeable_session_id() == results.session.id


def test_resume(populated_suite):
    fail_index = populated_suite.fail_in_middle()
    result = populated_suite.run(stop_on_error=True)

    save_resume_state(result.session.results)

    resumed = get_tests_to_resume(result.session.id)

    assert len(resumed) + result.session.results.get_num_started() - 1 == len(populated_suite)
    assert resumed[0].endswith(populated_suite[fail_index].function_name)
