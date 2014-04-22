from __future__ import absolute_import

import linecache
import os
import sys
import traceback
import types


def get_traceback_string(exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    exc_type, exc_value, exc_tb = exc_info  # pylint: disable=unpacking-non-sequence
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))


def distill_traceback(tb):

    returned = DistilledTraceback()
    while tb is not None:
        returned.frames.append(DistilledFrame(tb.tb_frame))
        tb = tb.tb_next
    return returned


class DistilledTraceback(object):

    def __init__(self):
        super(DistilledTraceback, self).__init__()
        self.frames = []

    @property
    def cause(self):
        if self.frames:
            return self.frames[-1]


class DistilledFrame(object):

    def __init__(self, frame):
        super(DistilledFrame, self).__init__()
        self.filename = os.path.abspath(frame.f_code.co_filename)
        self.lineno = frame.f_lineno
        self.func_name = frame.f_code.co_name
        self.locals = self._capture_locals(frame)
        self.globals = self._capture_globals(frame)
        self.code_line = linecache.getline(self.filename, self.lineno).rstrip()
        self.code_string = "".join(
            linecache.getline(self.filename, lineno)
            for lineno in range(frame.f_code.co_firstlineno, self.lineno + 1)) or None

    def _capture_globals(self, frame):
        used_globals = set(frame.f_code.co_names)
        return dict((global_name, {"value": _safe_repr(value)})
                    for global_name, value in frame.f_globals.items()
                    if global_name in used_globals and self._is_global_included(value))

    def _is_global_included(self, g):
        if isinstance(g, (types.FunctionType, types.MethodType, types.ModuleType, type)):
            return False
        return True

    def _capture_locals(self, frame):
        return dict((local_name, {"value": _safe_repr(value)})
                    for local_name, value in frame.f_locals.items())

def _safe_repr(value):
    try:
        return repr(value)
    except Exception:  # pylint: disable=broad-except
        return "[Unprintable {0!r} object]".format(type(value).__name__)
