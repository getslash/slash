from __future__ import print_function

import sys
import traceback

from .. import hooks as trigger_hook
from ..conf import config
from ..ctx import context
from .. import exceptions
from .pattern_matching import Matcher

import warnings

NO_EXC_INFO = (None, None, None)

def _debugger(debug_function_str, exc_info_transform=None, name=None):  # pragma: no cover
    module_name, function_name = debug_function_str.rsplit(".", 1)
    def debugger(exc_info):
        try:
            module = __import__(module_name, fromlist=[''])
        except ImportError:
            raise NotImplementedError() # pragma: no cover
        func = getattr(module, function_name)
        orig_exc_info = exc_info
        _notify_going_into_debugger(orig_exc_info)
        if orig_exc_info == NO_EXC_INFO:
            func = getattr(module, 'set_trace')
            func()
        else:
            if exc_info_transform is not None:
                exc_info = exc_info_transform(exc_info)
            func(*exc_info)
    debugger.__name__ = debug_function_str
    debugger.__external_name__ = name
    return debugger

def _notify_going_into_debugger(exc_info):
    if context.session is not None:
        context.session.reporter.report_before_debugger(exc_info)
    else:
        print('\nException caught in debugger: {}'.format(traceback.format_exception_only(exc_info[0], exc_info[1])[0].strip()))

def _only_tb(exc_info):  # pragma: no cover
    return (exc_info[2],)

def _tb_type_value(exc_info):  # pragma: no cover
    return (exc_info[2], exc_info[0], exc_info[1])

_KNOWN_DEBUGGERS = [
    # order is important here!
    _debugger("pudb.post_mortem", _tb_type_value, name='pudb'),
    _debugger("ipdb.post_mortem", _only_tb, name='ipdb'),
    _debugger("pdb.post_mortem", _only_tb, name='pdb'),
    ]


def debug_if_needed(exc_info=None):

    if not config.root.debug.enabled:
        return
    if exc_info is None:
        exc_info = sys.exc_info()
    if exc_info[0] is None:
        return
    if context.session and isinstance(exc_info[1], context.session.get_skip_exception_types()) and not config.root.debug.debug_skips:
        return
    if isinstance(exc_info[1], (SystemExit,) + exceptions.INTERRUPTION_EXCEPTIONS):
        return

    exc_repr = repr(exc_info[1])
    matchers = [Matcher(s) for s in config.root.debug.filter_strings]
    if matchers and not all(matcher.matches(exc_repr) for matcher in matchers):
        return
    launch_debugger(exc_info)


def launch_debugger(exc_info):
    trigger_hook.entering_debugger(exc_info=exc_info) # pylint: disable=no-member

    debugger_name = config.root.debug.debugger

    debuggers = list(_KNOWN_DEBUGGERS)
    if debugger_name is not None:
        for index, debugger in enumerate(debuggers):
            if debugger_name == debugger.__external_name__:
                debuggers.insert(0, debuggers.pop(index))
                break
        else:
            warnings.warn('Specified debugger {!r} is not a known debugger name'.format(debugger_name))

    for debug_func in debuggers:
        try:
            debug_func(exc_info)
        except NotImplementedError:   # pragma: no cover
            if debug_func.__external_name__ == debugger_name:
                warnings.warn('Specified debugger {!r} is not available'.format(debugger_name))
            continue
        else:
            break
    else:
        raise NotImplementedError("No debug function available")  # pragma: no cover
