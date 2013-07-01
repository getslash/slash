import operator
import sys
from ..conf import config
from ..exceptions import SkipTest

def _debugger(debug_function_str, exc_info_transform=None):
    module_name, function_name = debug_function_str.rsplit(".", 1)
    def debugger(exc_info):
        try:
            module = __import__(module_name, fromlist=[''])
        except ImportError:
            raise NotImplementedError() # pragma: no cover
        func = getattr(module, function_name)
        if exc_info_transform is not None:
            exc_info = exc_info_transform(exc_info)
        func(exc_info)
    debugger.__name__ = debug_function_str
    return debugger

_KNOWN_DEBUGGERS = [
    # order is important here!
    _debugger("pudb.post_mortem"),
    _debugger("ipdb.post_mortem", operator.itemgetter(2)),
    _debugger("pdb.post_mortem", operator.itemgetter(2)),
    ]


def debug_if_needed(exc_info=None):
    if not config.root.debug.enabled:
        return
    if exc_info is None:
        exc_info = sys.exc_info()
    if exc_info[0] is SkipTest and not config.root.debug.debug_skips:
        return
    for debug_func in _KNOWN_DEBUGGERS:
        try:
            debug_func(exc_info)
        except NotImplementedError:
            continue
        else:
            break
    else:
        # should never happen
        assert False, "No debug function available!"
