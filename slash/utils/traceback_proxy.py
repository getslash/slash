"""
This module contains the implementation of a traceback.traceback object proxy.
It is needed in order to make creation and modification of these objects possible,
which is not supported in Python by default, as they are quite internal types.
It lets us concatenate and fake tracebacks in case of handling an exception.
The manipulation of tracebacks is done using ctypes hacks and casting pointers to structs,
and works only with CPython.
"""

import sys
import traceback
import types
import ctypes
import inspect

from .._compat import PY2, PYPY

__all__ = ["create_traceback_proxy"]

if PYPY:
    def create_traceback_proxy(tb=None, frame_correction=0): # pylint: disable=unused-argument
        raise NotImplementedError("Tracebacks manipulation is not possible in PyPy")

else:
    class TracebackProxy(object):
        """
        Wraps the builtin traceback.traceback object.
        Exports exactly the same interface, making these types interchangable
        """

        if PY2:
            if hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
                _Py_ssize_t = ctypes.c_int64
            else:
                _Py_ssize_t = ctypes.c_int
        else:
            _Py_ssize_t = ctypes.c_ssize_t

        class _PyObject(ctypes.Structure):
            pass

        # Python build with "--with-pydebug"
        if hasattr(sys, 'getobjects'):
            _PyObject._fields_ = [ # pylint: disable=protected-access
                ('_ob_next', ctypes.POINTER(_PyObject)),
                ('_ob_prev', ctypes.POINTER(_PyObject)),
                ('ob_refcnt', _Py_ssize_t),
                ('ob_type', ctypes.POINTER(_PyObject))
            ]
        else:
            _PyObject._fields_ = [ # pylint: disable=protected-access
                ('ob_refcnt', _Py_ssize_t),
                ('ob_type', ctypes.POINTER(_PyObject))
            ]

        class _Frame(_PyObject):
            """
            Represents a traceback.frame object
            """
            pass

        class _Traceback(_PyObject):
            """
            Represents a traceback.traceback object
            """
            pass

        _Traceback._fields_ = [ # pylint: disable=protected-access
            ('tb_next', ctypes.POINTER(_Traceback)),
            ('tb_frame', ctypes.POINTER(_Frame)),
            ('tb_lasti', ctypes.c_int),
            ('tb_lineno', ctypes.c_int)
        ]

        def __init__(self, tb=None, frame=None):
            assert tb is not None or frame is not None
            self._tb = TracebackProxy.create_traceback()
            self._obj = TracebackProxy._Traceback.from_address(id(self._tb)) # pylint: disable=no-member
            self.tb_next = None
            if tb:
                self.tb_frame = tb.tb_frame
                self.tb_lasti = tb.tb_lasti
                self.tb_lineno = tb.tb_lineno
            else:
                self.tb_frame = frame
                self.tb_lasti = frame.f_lasti
                self.tb_lineno = frame.f_lineno

        def print_tb(self):
            traceback.print_tb(self._tb)

        @property
        def tb_next(self):
            return self._tb.tb_next

        @tb_next.setter
        def tb_next(self, tb):
            if self._tb.tb_next:
                old = TracebackProxy._Traceback.from_address(id(self._tb.tb_next)) # pylint: disable=no-member
                old.ob_refcnt -= 1

            assert tb is None or isinstance(tb, types.TracebackType) or isinstance(tb, TracebackProxy)
            if tb:
                obj = TracebackProxy._Traceback.from_address(id(tb)) # pylint: disable=no-member
                obj.ob_refcnt += 1
                self._obj.tb_next = ctypes.pointer(obj)
            else:
                self._obj.tb_next = ctypes.POINTER(TracebackProxy._Traceback)()

        @property
        def tb_frame(self):
            return self._tb.tb_frame

        @tb_frame.setter
        def tb_frame(self, frame):
            if self._tb.tb_frame:
                old = TracebackProxy._Frame.from_address(id(self._tb.tb_frame)) # pylint: disable=no-member
                old.ob_refcnt -= 1
            if frame:
                assert isinstance(frame, types.FrameType)
                frame = TracebackProxy._Frame.from_address(id(frame)) # pylint: disable=no-member
                frame.ob_refcnt += 1
                self._obj.tb_frame = ctypes.pointer(frame)
            else:
                self._obj.tb_frame = ctypes.POINTER(TracebackProxy._Frame)()

        @property
        def tb_lasti(self):
            return self._tb.tb_lasti

        @tb_lasti.setter
        def tb_lasti(self, lasti):
            self._obj.tb_lasti = lasti

        @property
        def tb_lineno(self):
            return self._tb.tb_lineno

        @tb_lineno.setter
        def tb_lineno(self, lineno):
            self._obj.tb_lineno = lineno

        def __eq__(self, other):
            return self._tb == other._tb # pylint: disable=protected-access

        def __ne__(self, other):
            return self._tb != other._tb # pylint: disable=protected-access

        @staticmethod
        def create_traceback():
            try:
                1 / 0
            except:
                tb = sys.exc_info()[2]
            return tb


    def create_traceback_proxy(tb=None, frame_correction=0):
        """
        Builds a TracebackProxy object, using a given traceback, or current context if None.
        Returns a tuple with the first and the last tracebacks.
        Works only on CPython (Both Python 2 and 3 are supported)
        :param tb: traceback.traceback object to extract frames from
        :param frame_correction: Specifies the amount of frames to skip
        """
        assert frame_correction >= 0
        if isinstance(tb, types.TracebackType):
            for i in range(frame_correction + 1): # pylint: disable=unused-variable
                first = current = TracebackProxy(tb=tb)
                tb = tb.tb_next
            while tb:
                current.tb_next = TracebackProxy(tb=tb)
                tb = tb.tb_next
                current = current.tb_next
        else:
            frame_correction += 1 # Compensate this call frame
            frames = [frame_info[0] for frame_info in inspect.stack()[frame_correction:]]
            frames.reverse()
            first = current = TracebackProxy(frame=frames[0])
            for frame in frames[1:]:
                current.tb_next = TracebackProxy(frame=frame)
                current = current.tb_next

        return (first, current)
