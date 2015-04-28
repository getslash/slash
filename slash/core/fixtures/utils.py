import functools
import itertools

from ..._compat import izip, iteritems
from ...utils.python import getargspec
from ...utils.function_marker import function_marker

_id_gen = itertools.count(1000)

def fixture(func=None, name=None, scope=None, autouse=False):
    if func is None:
        return functools.partial(fixture, name=name, scope=scope, autouse=autouse)

    if not hasattr(func, '__slash_fixture__'):
        func.__slash_fixture__ = FixtureInfo(func, name=name, scope=scope, autouse=autouse)

    return func

nofixtures = function_marker('__slash_nofixtures__')
nofixtures.__doc__ = 'Marks the decorated function as opting out of automatic fixture deduction. Slash will not attempt to parse needed fixtures from its argument list'


class FixtureInfo(object):

    def __init__(self, func=None, name=None, scope=None, autouse=False):
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
        self.autouse = autouse
        self.scope = _SCOPES[scope]
        if self.func is not None:
            self.required_args = getargspec(func).args
        else:
            self.required_args = []
        if 'this' in self.required_args:
            self.required_args.remove('this')
            self.needs_this = True
        else:
            self.needs_this = False

def get_scope_by_name(scope_name):
    return _SCOPES[scope_name]

def get_scope_name_by_scope(scope_id):
    return _SCOPES_BY_ID[scope_id]

_SCOPES = dict(
    izip(('test', 'module', 'session'), itertools.count()))

_SCOPES_BY_ID = dict((id, name) for (name, id) in iteritems(_SCOPES))
