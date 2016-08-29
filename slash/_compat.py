# -*- coding: utf-8 -*-

# Based on logbook.helpers, licensed under BSD. See https://github.com/mitsuhiko/logbook/blob/0.4.2/logbook/compat.py for copyright information

#pylint: disable=import-error
#pylint: disable=maybe-no-member
#pylint: disable=no-name-in-module
#pylint: disable=undefined-variable
#pylint: disable=unused-argument
#pylint: disable=unused-import
#pylint: disable=exec-used
import sys
from types import TracebackType

PY2 = sys.version_info[0] == 2
PYPY = hasattr(sys, 'pypy_version_info')

if PY2:
    from cStringIO import StringIO as cStringIO
else:
    from io import StringIO as cStringIO

if PY2:
    import __builtin__ as _builtins
else:
    import builtins as _builtins

try:
    import json
except ImportError:
    import simplejson as json

if PY2:
    from cStringIO import StringIO
    iteritems = lambda d: d.iteritems() # not dict.iteritems!!! we support ordered dicts as well
    itervalues = lambda d: d.itervalues()
    from itertools import imap
    reduce = _builtins.reduce
    from itertools import izip
    from itertools import izip_longest
    xrange = _builtins.xrange
else:
    from io import StringIO
    izip = _builtins.zip
    imap = _builtins.map
    from functools import reduce
    xrange = range
    iteritems = lambda d: iter(d.items()) # not dict.items!!! See above
    itervalues = lambda d: iter(d.values())
    from itertools import zip_longest as izip_longest

_IDENTITY = lambda obj: obj

if PY2:
    integer_types = (int, long)
    string_types = (basestring,)
else:
    integer_types = (int,)
    string_types = (str,)

if PY2:
    #Yucky, but apparently that's the only way to do this
    exec("""
def reraise(tp, value, tb=None):
    raise tp, value, tb
""", locals(), globals())
else:
    def reraise(tp, value, tb=None):
        # A hacky way to check, whether we have a TracebackProxy here. Can't check directly, as
        # it would lead to circular import.
        if value.__traceback__ is not tb:
            if not isinstance(tb, TracebackType):
                tb = tb._tb # pylint: disable=protected-access
            raise value.with_traceback(tb)
        raise value

try:
    from collections import OrderedDict # pylint: disable=E0611
except ImportError: # python 2.6
    from ordereddict import OrderedDict # pylint: disable=F0401

try:
    from contextlib import ExitStack #pylint: disable=E0611
except ImportError:
    from contextlib2 import ExitStack

if sys.version_info < (2, 7):

    def get_underlying_classmethod_function(func):
        returned = func.__get__(True)
        return getattr(returned, 'im_func', returned)

else:

    def get_underlying_classmethod_function(func):
        return func.__func__
