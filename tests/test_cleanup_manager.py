# pylint: disable=redefined-outer-name
import pytest
from slash.core.cleanup_manager import CleanupManager

from .conftest import Checkpoint


@pytest.mark.parametrize('in_failure', [True, False])
@pytest.mark.parametrize('in_interruption', [True, False])
def test_cleanup_default_scope(cleanup_manager, cleanup, in_failure, in_interruption):
    cleanup_manager.add_cleanup(cleanup)
    assert not cleanup.called
    cleanup_manager.call_cleanups(scope=cleanup_manager.latest_scope, in_failure=in_failure, in_interruption=in_interruption)

    assert cleanup.called == (not in_interruption)

def test_default_scope(cleanup_manager):
    cleanup1 = cleanup_manager.add_cleanup(Checkpoint())

    with cleanup_manager.scope('session'):

        cleanup2 = cleanup_manager.add_cleanup(Checkpoint())

        with cleanup_manager.scope('module'):

            cleanup3 = cleanup_manager.add_cleanup(Checkpoint())

            assert not cleanup3.called
        assert not cleanup2.called

    assert not cleanup1.called
    cleanup_manager.call_cleanups(scope=cleanup_manager.latest_scope, in_failure=False, in_interruption=False)
    assert cleanup1.called
    assert cleanup2.called
    assert cleanup3.called
    assert cleanup3.timestamp < cleanup2.timestamp < cleanup1.timestamp


@pytest.fixture
def cleanup_manager():
    returned = CleanupManager()
    returned.push_scope(None)
    return returned


@pytest.fixture
def cleanup(checkpoint):
    return checkpoint
