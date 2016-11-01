import operator
from contextlib import contextmanager

from ..._compat import iteritems
from ...utils.python import wraps, get_argument_names
from .fixture_base import FixtureBase
from .utils import FixtureInfo, get_scope_by_name

_PARAM_INFO_ATTR_NAME = '__slash_parametrize__'


def parametrize(parameter_name, values):
    """Decorator to create multiple test cases out of a single function or module, where the cases vary by the value of ``parameter_name``, as iterated through ``values``.
    """

    def decorator(func):

        params = getattr(func, _PARAM_INFO_ATTR_NAME, None)
        if params is None:
            params = ParameterizationInfo(func)

            @wraps(func, preserve=['__slash_fixture__'])
            def new_func(*args, **kwargs):
                # for better debugging. _current_variation gets set to None on context exit
                variation = _current_variation
                for name, param in params.iter_parametrization_fixtures():
                    value = variation.get_param_value(param)
                    if name not in kwargs:
                        kwargs[name] = value
                return func(*args, **kwargs)
            setattr(new_func, _PARAM_INFO_ATTR_NAME, params)
            returned = new_func
        else:
            returned = func

        params.add_options(parameter_name, values)
        return returned

    return decorator


def iterate(**kwargs):

    def decorator(func):
        for name, options in iteritems(kwargs):
            func = parametrize(name, options)(func)
        return func
    return decorator


def toggle(param_name):
    """A shortcut for :func:`slash.parametrize(param_name, [True, False]) <slash.parametrize>`

    .. note:: Also available for import as slash.parameters.toggle
    """
    return parametrize(param_name, (True, False))


_current_variation = None


@contextmanager
def bound_parametrizations_context(variation, fixture_store, fixture_namespace):
    global _current_variation  # pylint: disable=global-statement
    assert _current_variation is None
    _current_variation = variation
    try:
        fixture_store.activate_autouse_fixtures_in_namespace(fixture_namespace)
        _current_variation.populate_values()
        yield
    finally:
        _current_variation.forget_values()
        _current_variation = None


def iter_parametrization_fixtures(func):
    if isinstance(func, FixtureBase):
        func = func.fixture_func
    param_info = getattr(func, _PARAM_INFO_ATTR_NAME, None)
    if param_info is None:
        return []
    return param_info.iter_parametrization_fixtures()


class ParameterizationInfo(object):

    def __init__(self, func):
        super(ParameterizationInfo, self).__init__()
        self._argument_names = get_argument_names(func)
        self._argument_name_set = frozenset(self._argument_names)
        self._params = {}
        self._extra_params = {}
        self.path = '{}:{}'.format(func.__module__, func.__name__)

    def add_options(self, param_name, values):
        assert param_name not in self._params

        if not isinstance(param_name, (list, tuple)):
            names = (param_name,)
            values = [[v] for v in values]
        else:
            names = param_name
            values = list(values)
            for value_set in values:
                if not isinstance(value_set, (tuple, list)):
                    raise RuntimeError('Invalid parametrization value (expected sequence): {0!r}'.format(value_set))
                if len(value_set) != len(names):
                    raise RuntimeError('Invalid parametrization value (invalid length): {0!r}'.format(value_set))

        p = Parametrization(values=values, path='{}.{}'.format(self.path, param_name))
        for index, name in enumerate(names):
            if name in self._argument_name_set:
                params_dict = self._params
            else:
                params_dict = self._extra_params
            params_dict[name] = p.as_transform(operator.itemgetter(index))

    def iter_parametrization_fixtures(self):
        for name in self._argument_names:
            values = self._params.get(name)
            if values is not None:
                yield name, values
        for name, values in self._extra_params.items():
            yield name, values


def _id(obj):
    return obj


class Parametrization(FixtureBase):

    def __init__(self, path, values, info=None, transform=_id):
        super(Parametrization, self).__init__()
        self.path = path
        self.values = list(values)
        if info is None:
            info = FixtureInfo(path=path)
        self.info = info
        self.scope = get_scope_by_name('test')
        self.transform = transform

    def get_value(self, kwargs, active_fixture):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        raise NotImplementedError()  # pragma: no cover

    def _resolve(self, store):
        return {}

    def as_transform(self, transform):
        return Parametrization(values=self.values, info=self.info, transform=transform, path=self.path)
