import functools


def wraps(func):
    def decorator(new_func):
        returned = functools.wraps(func)(new_func)
        returned.__wraps__ = func
        return returned
    return decorator

def get_underlying_func(func):
    while True:
        underlying = getattr(func, "__wraps__", None)
        if underlying is None:
            return func
        func = underlying
