"""
Shakedown python compatibility library for cross-python support
"""
#pylint: disable=W0611
import sys

PY2 = (sys.version_info[0] == 2)

if PY2:
    from __builtin__ import xrange
else:
    xrange = range
