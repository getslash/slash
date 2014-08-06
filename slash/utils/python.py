import functools
import inspect

from sentinels import NOTHING


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
