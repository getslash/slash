from __future__ import absolute_import
import sys
import traceback

def get_traceback_string(exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    exc_type, exc_value, exc_tb = exc_info
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
