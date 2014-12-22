import itertools
import json
import os

import logbook

from .utils.path import ensure_directory

_logger = logbook.Logger(__name__)

_RESUME_DIR = os.path.expanduser("~/.slash/session_states")
_RESUME_COUNTER = itertools.count()
_MAX_NUM_SAVED_SESSIONS = 10

LATEST = object()


def save_resume_state(session_result):
    resume_filename = _generate_resume_filename(session_result.session.id)
    tmp_filename = resume_filename + ".tmp"
    ensure_directory(os.path.dirname(tmp_filename))
    with open(tmp_filename, "w") as f:
        json.dump({
            "tests": [
                {"address": str(result.test_metadata.address), "needs_rerun":
                 result.is_failure() or result.is_error() or not result.is_started()}
                for result in session_result.iter_test_results()
            ],
        }, f)
    os.rename(tmp_filename, resume_filename)
    _logger.debug('Saved resume state to {0}', resume_filename)
    _cleanup_old_files()


def get_last_resumeable_session_id():
    files = _get_resume_state_files_by_mtime()
    if not files:
        raise CannotResume("No resume files found")
    return _get_session_id_from_filename(files[0][1])

def _get_session_id_from_filename(filename):
    return os.path.basename(filename).split("_", 1)[1].rsplit(".", 1)[0]


def _cleanup_old_files():
    for _, deleted_filename in _get_resume_state_files_by_mtime()[_MAX_NUM_SAVED_SESSIONS:]:
        _logger.debug('Deleting old statefile {0!r}...', deleted_filename)
        os.unlink(deleted_filename)

def _get_resume_state_files_by_mtime():
    return sorted(
        ((os.stat(f).st_mtime, f) for f in
         [os.path.join(_RESUME_DIR, f) for f in os.listdir(_RESUME_DIR)]),
        reverse=True)


def get_tests_to_resume(session_id):
    resume_filename = _find_resume_file_by_session_id(session_id)
    try:
        with open(resume_filename) as f:
            state = json.load(f)

    except (IOError, OSError) as e:
        raise CannotResume(
            "Cannot resume session {0} ({1})".format(session_id, e))

    return [test["address"] for test in state["tests"] if test["needs_rerun"]]

def _generate_resume_filename(session_id):
    return os.path.join(_RESUME_DIR, "{0:03}_{1}".format(next(_RESUME_COUNTER), session_id)) + ".json"

def _find_resume_file_by_session_id(session_id):
    for _, filename in _get_resume_state_files_by_mtime():
        if _get_session_id_from_filename(filename) == session_id:
            return filename
    raise CannotResume("Could not find resume file for session {0}".format(session_id))

class CannotResume(Exception):
    pass
