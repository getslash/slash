import functools
import inspect
import itertools

from ..._compat import zip

_id_gen = itertools.count(1000)

def fixture(func=None, name=None, scope=None):
    if func is None:
        return functools.partial(fixture, name=name, scope=scope)

    if not hasattr(func, '__slash_fixture__'):
        func.__slash_fixture__ = FixtureInfo(func, name=name, scope=scope)

    return func

_PARAMETRIZE_NAME = '__slash_parametrize__'


def parametrize(parameter_name, values):
    def decorator(func):
        params = getattr(func, _PARAMETRIZE_NAME, None)
        if params is None:
            params = func.__slash_parametrize__ = {}
        params.setdefault(parameter_name, []).extend(values)
        return func
    return decorator


def get_parametrization(func):
    return getattr(func, _PARAMETRIZE_NAME, {})


class FixtureInfo(object):

    def __init__(self, func=None, name=None, scope=None):
        super(FixtureInfo, self).__init__()
        self.id = next(_id_gen)
        if name is None:
            if func is None:
                name = '__unnamed_{0}'.format(self.id)
            else:
                name = func.__name__
        if scope is None:
            scope = 'test'
        self.name = name
        self.func = func
        self.scope = _SCOPES[scope]
        if self.func is not None:
            self.required_args = inspect.getargspec(func).args
        else:
            self.required_args = []

def get_scope_by_name(scope_name):
    return _SCOPES[scope_name]

_SCOPES = dict(
    zip(('test', 'module', 'session'), itertools.count()))
