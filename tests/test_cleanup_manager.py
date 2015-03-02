import pytest
from slash.core.cleanup_manager import CleanupManager

from .conftest import Checkpoint


def test_cleanup_default_scope(cleanup_manager, cleanup):
    cleanup_manager.add_cleanup(cleanup)
    assert not cleanup.called
    cleanup_manager.call_cleanups()
    assert cleanup.called

def test_default_scope(cleanup_manager):
    cleanup1 = cleanup_manager.add_cleanup(Checkpoint())

    with cleanup_manager.scope('session'):

        cleanup2 = cleanup_manager.add_cleanup(Checkpoint())

        with cleanup_manager.scope('module'):

            cleanup3 = cleanup_manager.add_cleanup(Checkpoint())

            assert not cleanup3.called
        assert not cleanup2.called

    assert not cleanup1.called
    cleanup_manager.call_cleanups()
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
