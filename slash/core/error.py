import sys
import traceback

from .._compat import string_types
from ..utils.traceback_utils import distill_traceback
from ..exception_handling import is_exception_fatal


class Error(object):

    traceback = exception_type = exception = arg = None

    def __init__(self, msg=None, exc_info=None):
        super(Error, self).__init__()
        if msg is None and exc_info is not None:
            msg = traceback.format_exception_only(exc_info[0], exc_info[1])[0].strip()
        if not isinstance(msg, string_types):
            self.arg = msg
            msg = repr(msg)
        self.message = msg
        if exc_info is not None:
            self.exception_type, self.exception, tb = exc_info  # pylint: disable=unpacking-non-sequence
            self.traceback = distill_traceback(tb)

    def is_fatal(self):
        return self.exception is not None and is_exception_fatal(self.exception)

    @classmethod
    def capture_exception(cls):
        return cls(exc_info=sys.exc_info())

    @property
    def cause(self):
        if self.traceback is not None:
            return self.traceback.cause

    @property
    def filename(self):
        if self.traceback is not None:
            return self.traceback.cause.filename

    @property
    def lineno(self):
        if self.traceback is not None:
            return self.traceback.cause.lineno

    @property
    def func_name(self):
        if self.traceback is not None:
            return self.traceback.cause.func_name

    def __repr__(self):
        return self.message
