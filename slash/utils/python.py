import functools
import inspect
import sys

from sentinels import NOTHING

from .._compat import reraise


def wraps(func, preserve=()):
    def decorator(new_func):
        returned = functools.wraps(func)(new_func)
        returned.__wraps__ = func
        return returned
    for p in preserve:
        orig = getattr(func, p, NOTHING)
        if orig is not NOTHING:
            setattr(decorator, p, orig)
    return decorator

def get_underlying_func(func):
    while True:
        underlying = getattr(func, "__wraps__", None)
        if underlying is None:
            return func
        func = underlying

def getargspec(func):
    return inspect.getargspec(get_underlying_func(func))


def call_all_raise_first(_funcs, *args, **kwargs):
    exc_info = None
    for func in _funcs:
        try:
            func(*args, **kwargs)
        except Exception: # pylint: disable=broad-except
            exc_info = sys.exc_info()
    if exc_info is not None:
        reraise(*exc_info)
