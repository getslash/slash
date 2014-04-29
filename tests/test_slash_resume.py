import os
import time

import pytest
from slash import resuming
from slash.resuming import (_MAX_NUM_SAVED_SESSIONS, CannotResume, get_last_resumeable_session_id,
                            get_tests_to_resume, save_resume_state)


def test_resume_no_session():
    with pytest.raises(CannotResume):
        get_tests_to_resume("nonexisting_session")

def test_max_resumed_sessions(suite):
    for i in range(_MAX_NUM_SAVED_SESSIONS + 1):
        i += 1
        save_resume_state(suite.run())
        assert len(os.listdir(resuming._RESUME_DIR)) == min(_MAX_NUM_SAVED_SESSIONS, i)

def test_get_last_resumeable_session(suite):
    suite.fail_in_middle()
    prev_id = None
    for i in range(5):
        results = suite.run()
        assert results.session.id != prev_id
        prev_id = results.session.id
        save_resume_state(results)
        assert get_last_resumeable_session_id() == results.session.id


def test_resume(suite):
    fail_index = suite.fail_in_middle()
    result = suite.run(stop_on_error=True)

    save_resume_state(result)

    resumed = get_tests_to_resume(result.session.id)

    assert len(resumed) + result.get_num_started() - 1 == len(suite)
    assert resumed[0].endswith(suite[fail_index].method_name)
