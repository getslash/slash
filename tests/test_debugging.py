import sys

import pytest

import slash
from slash.exceptions import INTERRUPTION_EXCEPTIONS
from slash.utils import debug


def test_debug_if_needed_regular_exception(replaced_checkpoint, exc_info, debug_enabled):
    with slash.Session():
        debug.debug_if_needed(exc_info)
    assert replaced_checkpoint.called

def test_debug_if_needed_not_called(replaced_checkpoint, skipped_exc_info, debug_enabled):
    with slash.Session():
        debug.debug_if_needed(skipped_exc_info)
    assert not replaced_checkpoint.called


@pytest.fixture
def debug_enabled(config_override):
    config_override('debug.enabled', True)


@pytest.fixture(params=(SystemExit,) + INTERRUPTION_EXCEPTIONS)
def skipped_exc_info(request):
    try:
        raise request.param()
    except:
        return sys.exc_info()

@pytest.fixture
def exc_info():
    try:
        1/0
    except:
        return sys.exc_info()

@pytest.fixture
def replaced_checkpoint(checkpoint, forge):
    forge.replace_with(debug, 'launch_debugger', checkpoint)
    return checkpoint
