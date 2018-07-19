from __future__ import absolute_import

import inspect
import linecache
import os
import sys
import traceback
import types

from vintage import deprecated

from .._compat import PY2
from .. import context
from ..conf import config
from .python import get_underlying_func


_MAX_VARIABLE_VALUE_LENGTH = 100

_FILTERED_MEMBER_TYPES = [types.MethodType, types.FunctionType, type]
if PY2:
    _FILTERED_MEMBER_TYPES.append(types.UnboundMethodType) # pylint: disable=no-member
    _FILTERED_MEMBER_TYPES.append(types.ClassType) # pylint: disable=no-member
_FILTERED_MEMBER_TYPES = tuple(_FILTERED_MEMBER_TYPES)

_ALLOWED_ATTRIBUTE_TYPES = [int, str, float]
if PY2:
    _ALLOWED_ATTRIBUTE_TYPES.append(long) # pylint: disable=undefined-variable
_ALLOWED_ATTRIBUTE_TYPES = tuple(_ALLOWED_ATTRIBUTE_TYPES)


def get_traceback_string(exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    exc_type, exc_value, exc_tb = exc_info  # pylint: disable=unpacking-non-sequence
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))


def distill_traceback(tb, frame_correction=0, **kw):
    frames = _get_tb_frames(tb)
    if frame_correction:
        frames = frames[:len(frames) - frame_correction]
    return _distill_frames(frames, **kw)


def distill_call_stack(frame_correction=0, **kw):
    frames = _get_sys_trace_frames()
    if frame_correction:
        frames = frames[:len(frames) - frame_correction + 1]
    return _distill_frames(frames, **kw)


def _distill_frames(frames):
    returned = DistilledTraceback()
    repr_blacklisted_types = tuple(config.root.log.repr_blacklisted_types)
    for frame in frames:
        if isinstance(frame, tuple):
            frame, lineno = frame
        else:
            lineno = None
        if _is_frame_and_below_muted(frame):
            break
        if not _is_frame_muted(frame):
            returned.frames.append(DistilledFrame(frame, lineno, repr_blacklisted_types=repr_blacklisted_types))
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
        return self.to_string()

    def to_string(self, include_vars=False):
        return '\n'.join(frame.to_string(include_vars=include_vars) for frame in self.frames)


class DistilledFrame(object):

    def __init__(self, frame, lineno=None, repr_blacklisted_types=None):
        super(DistilledFrame, self).__init__()
        self.python_frame = frame
        self.filename = os.path.abspath(frame.f_code.co_filename)
        if lineno is None:
            lineno = frame.f_lineno
        self.lineno = lineno
        self.func_name = frame.f_code.co_name
        if repr_blacklisted_types is None:
            repr_blacklisted_types = tuple(config.root.log.repr_blacklisted_types)
        self._repr_blacklisted_types = repr_blacklisted_types
        self._locals = self._capture_locals(frame)
        self._globals = self._capture_globals(frame)
        self.code_line = linecache.getline(self.filename, self.lineno).rstrip()
        self.code_string = "".join(
            linecache.getline(self.filename, lineno)
            for lineno in range(frame.f_code.co_firstlineno, self.lineno + 1)) or None
        if context.test is not None:
            test_function = get_underlying_func(context.test.get_test_function())
            self._is_in_test_code = frame.f_code is test_function.__code__
        else:
            self._is_in_test_code = False

    @property
    @deprecated(since='1.5.0')
    def locals(self):
        return self._locals

    @property
    @deprecated(since='1.5.0')
    def globals(self):
        return self._globals

    def forget_python_frame(self):
        self.python_frame = None

    def is_in_test_code(self):
        return self._is_in_test_code

    def to_dict(self):
        serialized = {}
        for attr in ['filename', 'lineno', 'func_name', 'code_line', 'code_string']:
            serialized[attr] = getattr(self, attr)
        serialized['globals'] = self._globals
        serialized['locals'] = self._locals
        serialized['is_in_test_code'] = self._is_in_test_code
        return serialized

    def _capture_globals(self, frame):
        used_globals = set(frame.f_code.co_names)
        return dict((global_name, {"value": _safe_repr(value, self._repr_blacklisted_types)})
                    for global_name, value in frame.f_globals.items()
                    if global_name in used_globals and self._is_global_included(value))

    def _is_global_included(self, g):
        if isinstance(g, (types.FunctionType, types.MethodType, types.ModuleType, type)):
            return False
        return True

    def _capture_locals(self, frame):
        return dict((local_name, {"value": _safe_repr(local_value, self._repr_blacklisted_types)})
                    for key, value in frame.f_locals.items()
                    if "@" not in key
                    for local_name, local_value in self._unwrap_local(key, value, self._repr_blacklisted_types))

    def _unwrap_local(self, local_name, local_value, repr_blacklisted_types):
        yield local_name, local_value
        if local_name != 'self' or isinstance(local_value, repr_blacklisted_types):
            return

        for attr, value in iter_distilled_object_attributes(local_value):
            yield 'self.{}'.format(attr), value

    def __repr__(self):
        return self.to_string()

    def to_string(self, include_vars=False):
        returned = '  {0.filename}, line {0.lineno}:\n'.format(self)
        returned += '    {.code_line}'.format(self)
        if include_vars and self.python_frame is not None:
            for name, value in _unwrap_self_locals(self.python_frame.f_locals.items(), self._repr_blacklisted_types):
                returned += '\n\t- {}: {}'.format(name, _safe_repr(value, self._repr_blacklisted_types, truncate=False))
            returned += '\n'
        return returned


def _unwrap_self_locals(local_pairs, blacklisted_types):
    for name, value in local_pairs:

        yield name, value
        if name == 'self' and not isinstance(value, blacklisted_types):
            for attr_name, attr_value in iter_distilled_object_attributes(value):
                yield 'self.{}'.format(attr_name), attr_value


def iter_distilled_object_attributes(obj):
    try:
        obj_dict = getattr(obj, '__dict__', {})
    except Exception:       # pylint: disable=broad-except
        obj_dict = {}

    for attr in obj_dict:
        if attr.startswith('__') and attr.endswith('__'):
            continue
        try:
            value = getattr(obj, attr)
        except Exception:   # pylint: disable=broad-except
            continue
        if isinstance(value, _FILTERED_MEMBER_TYPES):
            continue
        yield attr, value


def distill_object_attributes(obj, truncate=True):
    repr_blacklisted_types = tuple(config.root.log.repr_blacklisted_types)
    return {attr: value if isinstance(value, _ALLOWED_ATTRIBUTE_TYPES) else _safe_repr(value, repr_blacklisted_types,
                                                                                       truncate=truncate)
            for attr, value in iter_distilled_object_attributes(obj)}


def _safe_repr(value, blacklisted_types, truncate=True):
    if blacklisted_types and isinstance(value, blacklisted_types):
        returned = _format_repr_skip_string(value)
    else:
        try:
            returned = repr(value)
        except Exception:  # pylint: disable=broad-except
            returned = "[Unprintable {!r} object]".format(type(value).__name__)

    if truncate and len(returned) > _MAX_VARIABLE_VALUE_LENGTH:
        returned = returned[:_MAX_VARIABLE_VALUE_LENGTH - 3] + '...'
    return returned


def _format_repr_skip_string(value):
    return "<{!r} object {:x}>".format(type(value).__name__, id(value))
