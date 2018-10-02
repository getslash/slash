from __future__ import print_function

import signal
import sys
import traceback
from slash import skip_test, context

from ...utils.debug import launch_debugger
from ..interface import PluginInterface

_PLUGIN_NAME = "signal handling"

_signal_handlers = {}

def register_handler(signal_name, skip_plugin=False):
    def register_handler_func(func):
        signal_no = getattr(signal, signal_name, None)
        if signal_no is not None:
            _signal_handlers[signal_no] = func
            if not skip_plugin:
                from ..plugin_manager import manager
                plugin = manager.get_active_plugins().get(_PLUGIN_NAME)
                if plugin:
                    plugin._set_handler(signal_no, func)  # pylint: disable=protected-access
        return func
    return register_handler_func


@register_handler('SIGUSR1', skip_plugin=True)
def _usr1_handler(*_, **__):
    if not sys.stdout.isatty():
        message = "Running without TTY when {!r} plugin caught SIGUSR1. Current stack:".format(_PLUGIN_NAME)
        if context.session is None:
            print(message)
        else:
            context.session.reporter.report_message(message)
            traceback.print_stack()
    else:
        launch_debugger(exc_info=(None, None, None))


@register_handler('SIGUSR2', skip_plugin=True)
def _usr2_handler(*_, **__):
    skip_test("Skipped due to SIGUSR2 signal caught by {!r} plugin".format(_PLUGIN_NAME))


class Plugin(PluginInterface):

    def __init__(self):
        super(Plugin, self).__init__()
        self._orig_handlers = {}

    def get_name(self):
        return _PLUGIN_NAME

    def _set_handler(self, signal_no, signal_handler):
        # This method is used by register_handler as well
        # It cannot be public due to import-loop while importing "registers_on" before
        # PluginManager initialization finished (it creates all builtin plugins on init)
        self._orig_handlers[signal_no] = signal.signal(signal_no, signal_handler)

    def activate(self):
        super().activate()
        for (sig_no, sig_handler) in _signal_handlers.items():
            self._set_handler(sig_no, sig_handler)

    def deactivate(self):
        super().deactivate()
        for sig_no, sig_handler in self._orig_handlers.items():
            signal.signal(sig_no, sig_handler)
        self._orig_handlers.clear()
