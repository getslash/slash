import sys
import traceback
from .._compat import string_types

class Error(object):

    def __init__(self, exc_info_or_msg):
        super(Error, self).__init__()
        if not isinstance(exc_info_or_msg, tuple):
            exc_info = sys.exc_info()
            if isinstance(exc_info_or_msg, string_types):
                message = exc_info_or_msg
            else:
                message = None
        else:
            exc_info = exc_info_or_msg
            message = None
        self.arg = exc_info_or_msg
        self.exception_type, self.exception, tb = exc_info
        self.message = message
        if tb is not None:
            self.exception_text = "".join(traceback.format_exception(
                self.exception_type, self.exception, tb
            ))
        else:
            self.exception_text = None

    def __repr__(self):
        return repr(self.exception)

    def __str__(self):
        return str(self.exception)
