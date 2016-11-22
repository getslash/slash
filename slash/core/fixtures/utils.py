import functools
import itertools

from sentinels import NOTHING

from ...ctx import context
from ..._compat import izip, iteritems
from ...utils.python import get_arguments_dict, wraps
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

    def __init__(self, func=None, name=None, scope=None, autouse=False, path=None):
        super(FixtureInfo, self).__init__()
        self.path = path
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

            self.required_args = get_arguments_dict(self.func)
        else:
            self.required_args = {}
        if 'this' in self.required_args:
            self.required_args.pop('this')
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


def generator_fixture(func):
    """A utility for generating parametrization values from a generator:

    >>> @slash.generator_fixture
    ... def some_parameter():
    ...     yield first_value
    ...     yield second_value

    .. note:: A generator parameter is a shortcut for a simple parametrized fixture, so the entire iteration is exhausted during test load time
    """
    from .parameters import parametrize

    @parametrize('param', list(func()))
    def new_func(param):
        return param

    new_func.__name__ = func.__name__

    return fixture(new_func)

def yield_fixture(func=None, **kw):
    """Builds a fixture out of a generator. The pre-yield part of the generator is used as the setup, where the
    yielded value becomes the fixture value. The post-yield part is added as a cleanup:

    >>> @slash.yield_fixture
    ... def some_fixture(arg1, arg2):
    ...     m = Microwave()
    ...     m.turn_on(wait=True)
    ...     yield m
    ...     m.turn_off()
    """

    if func is None:
        return functools.partial(yield_fixture, **kw)

    func = func
    @fixture(**kw)
    @wraps(func)
    def new_func(**kwargs):
        f = func(**kwargs)
        value = next(f)
        @context.fixture.add_cleanup
        def cleanup(): # pylint: disable=unused-variable
            try:
                next(f)
            except StopIteration:
                pass
            else:
                raise RuntimeError('Yielded fixture did not stop at cleanup')
        return value
    return new_func

class use(object):
    """Allows tests to use fixtures under different names

    def test_something(m: use('microwave')):
        ...
    """

    def __init__(self, real_fixture_name):
        super(use, self).__init__()
        self.real_fixture_name = real_fixture_name


def get_real_fixture_name_from_argument(argument):
    if argument.annotation is not NOTHING and isinstance(argument.annotation, use):
        return argument.annotation.real_fixture_name
    return argument.name


__all__ = ['fixture', 'nofixtures', 'generator_fixture', 'yield_fixture', 'use']
