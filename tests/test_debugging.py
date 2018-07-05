# pylint: disable=redefined-outer-name
import sys

import pytest

import slash
from slash.exceptions import INTERRUPTION_EXCEPTIONS
from slash.utils import debug


@pytest.mark.usefixtures("debug_enabled")
def test_debug_if_needed_regular_exception(replaced_checkpoint, exc_info):
    with slash.Session():
        debug.debug_if_needed(exc_info)
    assert replaced_checkpoint.called


@pytest.mark.usefixtures("debug_enabled")
def test_debug_if_needed_not_called(replaced_checkpoint, skipped_exc_info):
    with slash.Session():
        debug.debug_if_needed(skipped_exc_info)
    assert not replaced_checkpoint.called


@pytest.mark.usefixtures("debug_enabled")
def test_debug_if_needed_without_session(exc_info, replaced_checkpoint):
    debug.debug_if_needed(exc_info)
    assert replaced_checkpoint.called


@pytest.mark.parametrize('filter_strings,should_pdb', [
    (['division by zero',], True),
    (["not 'division by zero'",], False),
    (['ZeroDivisionError',], True),
    (['not ZeroDivisionError',], False),
    (['Zero', 'by'], True),
    (['Zero', 'foobar'], False),
    (['ZERO',], False),
])
def test_pdb_filtering(filter_strings, should_pdb, replaced_checkpoint, exc_info, config_override):
    config_override('debug.enabled', True)
    config_override('debug.filter_strings', filter_strings)
    with slash.Session():
        debug.debug_if_needed(exc_info)
    assert replaced_checkpoint.called == should_pdb


def test_pdb_filtering_with_disabled_debug(replaced_checkpoint, exc_info, config_override):
    config_override('debug.enabled', False)
    config_override('debug.filter_strings', ['ZeroDivisionError'])
    with slash.Session():
        debug.debug_if_needed(exc_info)
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
