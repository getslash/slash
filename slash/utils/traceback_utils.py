from __future__ import absolute_import

import inspect
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


def distill_traceback(tb, **kw):
    return _distill_frames(_get_tb_frames(tb), **kw)


def distill_call_stack(**kw):
    return _distill_frames(_get_sys_trace_frames(), **kw)


def _distill_frames(frames, frame_correction=0):
    returned = DistilledTraceback()
    frames = frames[:len(frames)-frame_correction+1]
    for frame in frames:
        if isinstance(frame, tuple):
            frame, lineno = frame
        else:
            lineno = None
        if _is_frame_and_below_muted(frame):
            break
        if not _is_frame_muted(frame):
            returned.frames.append(DistilledFrame(frame, lineno))
    return returned


def _get_tb_frames(tb):
    returned = []
    while tb is not None:
        returned.append((tb.tb_frame, tb.tb_lineno))
        tb = tb.tb_next
    return returned

def _get_sys_trace_frames():
    return [f[0] for f in reversed(inspect.stack()[:-1])]

def _is_frame_muted(frame):
    try:
        return _deduce_frame_function(frame) in _MUTED_LOCATIONS
    finally:
        del frame


def _deduce_frame_function(frame):
    try:
        frame_module = _deduce_frame_module(frame)
        if frame_module is None:
            return None

        return (frame_module, frame.f_code.co_name)
    finally:
        del frame


def _deduce_frame_module(frame):
    return frame.f_globals.get("__name__")


_MUTED_LOCATIONS = set([
    ("slash.core.function_test", "run"),
    ("slash.core.test", "run"),
    ("slash.exception_handling", "handling_exceptions"),
    ("slash.core.fixtures.fixture_store", "call_with_fixtures"),
    ("slash.frontend.main", "__main__"),
    ("slash.frontend.main", "main"),
    ("slash.frontend.main", "main_entry_point"),
    ("slash.frontend.slash_run", "slash_run"),
    ("slash.runner", "run_tests"),
    ("slash.runner", "_run_single_test"),
    ("slash.core.cleanup_manager", "call_cleanups"),
    ("slash.core.cleanup_manager", "__call__"),
])


def _is_frame_and_below_muted(frame):
    return frame.f_globals.get("__name__") in _MUTE_BELOW_MODULES

_MUTE_BELOW_MODULES = set([
    "slash.assertions"
])


class DistilledTraceback(object):

    def __init__(self):
        super(DistilledTraceback, self).__init__()
        self.frames = []

    def to_list(self):
        return [frame.to_dict() for frame in self.frames]

    @property
    def cause(self):
        if self.frames:
            return self.frames[-1]

    def __repr__(self):
        return '\n'.join(str(frame) for frame in self.frames)


class DistilledFrame(object):

    def __init__(self, frame, lineno=None):
        super(DistilledFrame, self).__init__()
        self.filename = os.path.abspath(frame.f_code.co_filename)
        if lineno is None:
            lineno = frame.f_lineno
        self.lineno = lineno
        self.func_name = frame.f_code.co_name
        self.locals = self._capture_locals(frame)
        self.globals = self._capture_globals(frame)
        self.code_line = linecache.getline(self.filename, self.lineno).rstrip()
        self.code_string = "".join(
            linecache.getline(self.filename, lineno)
            for lineno in range(frame.f_code.co_firstlineno, self.lineno + 1)) or None

    def to_dict(self):
        serialized = {}
        for attr in ['filename', 'lineno', 'func_name', 'locals', 'globals', 'code_line', 'code_string']:
            serialized[attr] = getattr(self, attr)
        return serialized

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
                    for local_name, value in frame.f_locals.items()
                    if "@" not in local_name)

    def __repr__(self):
        return '{0.filename}, line {0.lineno}:\n    {0.code_line}'.format(self)


def _safe_repr(value):
    try:
        return repr(value)
    except Exception:  # pylint: disable=broad-except
        return "[Unprintable {0!r} object]".format(type(value).__name__)
