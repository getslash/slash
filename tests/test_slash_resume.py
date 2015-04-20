import os
import time
from tempfile import mkdtemp

import pytest
from slash import resuming
from slash.resuming import (_MAX_NUM_SAVED_SESSIONS, CannotResume,
                            get_last_resumeable_session_id, get_tests_to_resume,
                            save_resume_state)


@pytest.fixture
def patched_resume_dir(forge):
    path = mkdtemp()
    forge.replace_with(resuming, '_RESUME_DIR', path)
    return path


def test_resume_no_session():
    with pytest.raises(CannotResume):
        get_tests_to_resume("nonexisting_session")


def test_max_resumed_sessions(suite, patched_resume_dir):
    for i in range(1, _MAX_NUM_SAVED_SESSIONS + 2):
        summary = suite.run()
        assert len(os.listdir(patched_resume_dir)) == min(_MAX_NUM_SAVED_SESSIONS, i)


def test_get_last_resumeable_session(suite):
    suite[len(suite) // 2].when_run.fail()
    prev_id = None
    for i in range(5):
        results = suite.run()
        assert results.session.id != prev_id
        prev_id = results.session.id
        save_resume_state(results.session.results)
        assert get_last_resumeable_session_id() == results.session.id


def test_resume(suite):
    fail_index = len(suite) // 2
    suite[fail_index].when_run.fail()
    for index, test in enumerate(suite):
        if index > fail_index:
            test.expect_not_run()
    result = suite.run(additional_args=['-x'])

    save_resume_state(result.session.results)

    resumed = get_tests_to_resume(result.session.id)

    assert len(resumed) + result.session.results.get_num_started() - 1 == len(suite)
    assert resumed[0].endswith(suite[fail_index].id)
