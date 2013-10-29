from .utils.callback import Callback
from .exceptions import HookAlreadyExists
from . import _compat

session_start = Callback(doc="Called right after session starts")
session_end   = Callback(doc="Called right before the session ends, regardless of the reason for termination")

after_session_start = Callback(doc="Second entry point for session start, useful for plugins relying on other plugins' session_start routine")

test_interrupt = Callback(doc="Called when a test is interrupted by a KeyboardInterrupt or other similar means")
test_start   = Callback(doc="Called right after a test starts")
test_end     = Callback(doc="Called right before a test ends, regardless of the reason for termination")
test_success = Callback(doc="Called on test success")
test_error   = Callback(doc="Called on test error")
test_failure = Callback(doc="Called on test failure")
test_skip    = Callback(doc="Called on test skip", arg_names=("reason",))

result_summary = Callback(doc="Called at the end of the execution, when printing results")

exception_caught_before_debugger = Callback(
    doc="Called whenever an exception is caught, but a debugger hasn't been entered yet"
)
exception_caught_after_debugger = Callback(
    doc="Called whenever an exception is caught, and a debugger has already been run"
)

_CUSTOM_HOOKS = {}

def add_custom_hook(hook_name):
    """
    Adds an additional hook to the set of available hooks
    """
    globs = globals()
    if hook_name in _CUSTOM_HOOKS or hook_name in globs:
        raise HookAlreadyExists("Hook named {0!r} already exists!".format(hook_name))

    returned = _CUSTOM_HOOKS[hook_name] = globs[hook_name] = Callback()
    return returned

def ensure_custom_hook(hook_name):
    """
    Like :func:`.add_custom_hook`, only forgives if the hook already exists
    """
    if hook_name in _CUSTOM_HOOKS:
        return _CUSTOM_HOOKS[hook_name]
    return add_custom_hook(hook_name)

def remove_custom_hook(hook_name):
    """
    Removes a hook from the set of available hooks
    """
    _CUSTOM_HOOKS.pop(hook_name)
    globals().pop(hook_name)

def get_custom_hook_names():
    """
    Retrieves the names of all custom hooks currently installed
    """
    return list(_CUSTOM_HOOKS)

def get_all_hooks():
    for name, callback in _compat.iteritems(globals()):
        if not isinstance(callback, Callback):
            continue
        yield name, callback

def get_hook_by_name(hook_name):
    """
    Returns a hook (if exists) by its name, otherwise returns None
    """
    return _CUSTOM_HOOKS.get(hook_name, None)

