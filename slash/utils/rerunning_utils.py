import os
import json
from .path import ensure_directory
from ..conf import config

def save_session_state(state):
    path = _get_path()
    ensure_directory(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(state, f)

def get_last_session_state():
    with open(_get_path(), "r") as f:
        return json.load(f)

def _get_path():
    return os.path.expanduser(config.root.run.session_state_path)
