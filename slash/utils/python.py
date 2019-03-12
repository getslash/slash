from collections import OrderedDict
import functools
import warnings
import inspect
import sys
import ast
import pickle

from sentinels import NOTHING

from .._compat import reraise, PY2, PYPY

def check_duplicate_functions(path):
    code = None
    with open(path) as f:
        code = f.read()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        root = ast.parse(code, filename=path)
    func_names = set()
    duplicates = set()
    for node in root.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in func_names:
                duplicates.add((path, node.name, node.lineno))
            else:
                func_names.add(node.name)
    return duplicates


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

def unpickle(thing):
    if not thing:
        return thing
    if PY2:
        return pickle.loads(thing)
    else:
        return pickle.loads(thing.data)

def get_underlying_func(func):
    while True:
        underlying = getattr(func, "__wraps__", None)
        if underlying is None:
            return func
        func = underlying


def get_argument_names(func):
    return [arg.name for arg in get_arguments(func)]


def get_arguments_dict(func):
    returned = OrderedDict()
    for arg in get_arguments(func):
        returned[arg.name] = arg
    return returned


def get_arguments(func):
    if PY2 or PYPY:
        func = get_underlying_func(func)
        spec = inspect.getargspec(func)  # pylint: disable=deprecated-method
        returned = [FunctionArgument(name=name) for name in spec.args]
    else:
        if getattr(func, '__self__', None) is not None:
            func = func.__func__ # signature() doesn't work on bound methods
        returned = [FunctionArgument.from_parameter(p) for name, p in inspect.signature(func).parameters.items()] # pylint: disable=no-member

    if returned and returned[0].name == 'self':
        returned = returned[1:]
    return returned


class FunctionArgument(object):

    def __init__(self, name, annotation=NOTHING):
        super(FunctionArgument, self).__init__()
        self.name = name
        self.annotation = annotation

    @classmethod
    def from_parameter(cls, parameter):
        annotation = parameter.annotation
        if annotation is parameter.empty:
            annotation = NOTHING
        return cls(name=parameter.name, annotation=parameter.annotation)


def call_all_raise_first(_funcs, *args, **kwargs):
    exc_info = None
    for func in _funcs:
        try:
            func(*args, **kwargs)
        except Exception:  # pylint: disable=broad-except
            exc_info = sys.exc_info()
    if exc_info is not None:
        reraise(*exc_info)
