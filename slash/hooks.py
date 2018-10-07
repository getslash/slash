import gossip
from vintage import deprecated

from .conf import config


def register(func):
    """A shortcut for registering hook functions by their names
    """
    return gossip.register('slash.{}'.format(func.__name__))(func)


def _deprecated_to_gossip(func):
    return deprecated(since="0.6.0", message="Use gossip instead")(func)

def _define(hook_name, **kwargs):
    hook = gossip.define("slash.{}".format(hook_name), **kwargs)
    globals()[hook_name] = hook
    return hook

_define('session_start', doc="Called right after session starts")
_define('session_end', doc="Called right before the session ends, regardless of the reason for termination")
_define('session_interrupt', doc='Called when the session is interrupted unexpectedly')

_define('tests_loaded', doc='Called when Slash finishes loading a batch of tests for execution (not necessarily al tests)', arg_names=('tests',))

_define('before_session_start', doc="Entry point which is called before session_start, useful for configuring plugins and other global resources")
_define('after_session_start', doc="Second entry point for session start, useful for plugins relying on other plugins' session_start routine")

_define('before_session_cleanup', doc="Called right before session cleanup begins")
_define('after_session_end', doc="Called right after session_end hook")

_define('app_quit', doc="Called right before the app quits")

_define('configure', doc='Configuration hook that happens during commandline parsing, and before plugins are activated. It is a convenient point to override plugin activation settings')  # pylint: disable=line-too-long

_define('test_interrupt', doc="Called when a test is interrupted by a KeyboardInterrupt or other similar means")
_define('test_avoided', doc="Called when a test is skipped completely (not even started)", arg_names=('reason',))
_define('test_start', doc="Called right after a test starts")
_define('test_distributed', doc="Called in parallel mode, after the parent sent a test to child)", arg_names=('test_logical_id', 'worker_session_id',)) # pylint: disable=line-too-long
_define('test_end', doc="Called right before a test ends, regardless of the reason for termination")
_define('log_file_closed', doc="Called right after a log file was closed", arg_names=('path', 'result',))
_define('before_test_cleanups', doc="Called right before a test cleanups are executed")
_define('test_success', doc="Called on test success")
_define('test_error', doc="Called on test error")
_define('test_failure', doc="Called on test failure")
_define('test_skip', doc="Called on test skip", arg_names=("reason",))
_define('worker_connected', doc="Called on new worker startup", arg_names=("session_id",))

_define('error_added', doc='Called when an error is added to a result (either test result or global)', arg_names=('error', 'result'))
_define('interruption_added', doc='Called when an exception is encountered that triggers test or session interruption',
        arg_names=('result', 'exception'))
_define('fact_set', doc='Called when a fact is set for a test', arg_names=['name', 'value'])
_define('warning_added', doc='Called when a warning is captured by Slash', arg_names=('warning',))

_define('result_summary', doc="Called at the end of the execution, when printing results")

_define('exception_caught_before_debugger',
        doc="Called whenever an exception is caught, but a debugger hasn't been entered yet")
_define('entering_debugger', doc='Called right before entering debugger', arg_names=('exc_info',))

_define('exception_caught_after_debugger',
        doc="Called whenever an exception is caught, and a debugger has already been run")
_define('before_worker_start', doc="Called in parallel execution mode, before the parent starts the child worker",
        arg_names=("worker_config",))

_define('prepare_notification', doc='Called with a message object prior to it being sent via the notifications plugin (if enabled)',
        arg_names=("message",))

_define('before_interactive_shell', doc='Called before starting interactive shell', arg_names=("namespace",))

_slash_group = gossip.get_group('slash')
_slash_group.set_strict()
_slash_group.set_exception_policy(gossip.RaiseDefer())

@gossip.register('gossip.on_handler_exception') # pylint: disable=unused-argument
def debugger(handler, exception, hook): # pylint: disable=unused-argument
    from .exception_handling import handle_exception

    if hook.group is _slash_group and config.root.debug.debug_hook_handlers:
        handle_exception(exception)

@_deprecated_to_gossip
def add_custom_hook(hook_name):
    """
    Adds an additional hook to the set of available hooks
    """
    return _define(hook_name)

@_deprecated_to_gossip
def ensure_custom_hook(hook_name):
    """
    Like :func:`.add_custom_hook`, only forgives if the hook already exists
    """
    try:
        return gossip.get_hook("slash.{}".format(hook_name))
    except LookupError:
        return _define(hook_name)

@_deprecated_to_gossip
def remove_custom_hook(hook_name):
    """
    Removes a hook from the set of available hooks
    """
    gossip.get_hook("slash.{}".format(hook_name)).undefine()
    globals().pop(hook_name)

@_deprecated_to_gossip
def get_custom_hook_names():
    """
    Retrieves the names of all custom hooks currently installed
    """
    raise NotImplementedError()  # pragma: no cover

@_deprecated_to_gossip
def get_all_hooks():
    return [
        (hook.name, hook)
        for hook in gossip.get_group('slash').get_hooks()]

@_deprecated_to_gossip
def get_hook_by_name(hook_name):
    """
    Returns a hook (if exists) by its name, otherwise returns None
    """
    return gossip.get_hook('slash.{}'.format(hook_name))
