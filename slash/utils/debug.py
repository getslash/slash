from __future__ import print_function

import sys
import traceback

from .. import hooks as trigger_hook
from ..conf import config
from ..exceptions import INTERRUPTION_EXCEPTIONS
from ..ctx import context


def _debugger(debug_function_str, exc_info_transform=None):  # pragma: no cover
    module_name, function_name = debug_function_str.rsplit(".", 1)
    def debugger(exc_info):
        try:
            module = __import__(module_name, fromlist=[''])
        except ImportError:
            raise NotImplementedError() # pragma: no cover
        func = getattr(module, function_name)
        orig_exc_info = exc_info
        if exc_info_transform is not None:
            exc_info = exc_info_transform(exc_info)
        _notify_going_into_debugger(orig_exc_info)
        func(*exc_info)
    debugger.__name__ = debug_function_str
    return debugger

def _notify_going_into_debugger(exc_info):
    if context.session is not None:
        context.session.reporter.report_before_debugger(exc_info)
    else:
        print('\nException caught in debugger: {0}'.format(traceback.format_exception_only(exc_info[0], exc_info[1])[0].strip()))

def _only_tb(exc_info):  # pragma: no cover
    return (exc_info[2],)

def _tb_type_value(exc_info):  # pragma: no cover
    return (exc_info[2], exc_info[0], exc_info[1])

_KNOWN_DEBUGGERS = [
    # order is important here!
    _debugger("pudb.post_mortem", _tb_type_value),
    _debugger("ipdb.post_mortem", _only_tb),
    _debugger("pdb.post_mortem", _only_tb),
    ]


def debug_if_needed(exc_info=None):

    if not config.root.debug.enabled:
        return
    if exc_info is None:
        exc_info = sys.exc_info()
    if isinstance(exc_info[1], context.session.get_skip_exception_types()) and not config.root.debug.debug_skips:
        return
    if isinstance(exc_info[1], (SystemExit,) + INTERRUPTION_EXCEPTIONS):
        return

    launch_debugger(exc_info)

def launch_debugger(exc_info):
    trigger_hook.entering_debugger(exc_info=exc_info) # pylint: disable=no-member

    for debug_func in _KNOWN_DEBUGGERS:
        try:
            debug_func(exc_info)
        except NotImplementedError:   # pragma: no cover
            continue
        else:
            break
    else:
        raise NotImplementedError("No debug function available")  # pragma: no cover
