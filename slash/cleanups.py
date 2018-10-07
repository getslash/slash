import functools

from .core import cleanup_manager
from .ctx import context


@functools.wraps(cleanup_manager.CleanupManager.add_cleanup)
def add_cleanup(*args, **kwargs):
    if context.session is None or context.session.cleanups is None:
        raise RuntimeError('Adding cleanups requires an active session')
    return context.session.cleanups.add_cleanup(*args, **kwargs)


def add_critical_cleanup(_func, *args, **kwargs):
    """
    Same as :func:`.add_cleanup`, only the cleanup will be called even on interrupted tests
    """
    return add_cleanup(_func, critical=True, *args, **kwargs)


def add_success_only_cleanup(_func, *args, **kwargs):
    """
    Same as :func:`.add_cleanup`, only the cleanup will be called only if the test succeeds
    """
    return add_cleanup(_func, success_only=True, *args, **kwargs)


def get_current_cleanup_phase():
    """
    Returns the current cleanup stage the session is currently in. This can return any
    one of the cleanup scopes supported by Slash, or ``None`` if no cleanups are currently in
    progress
    """
    if context.session is None or context.session.cleanups is None:
        return None
    return context.session.cleanups.get_current_scope_name()


def is_in_cleanup():
    """
    Returns ``True`` if the session is currently performing any cleanups
    """
    return get_current_cleanup_phase() is not None
