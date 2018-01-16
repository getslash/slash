import operator
import re
from contextlib import contextmanager
from sentinels import NOTHING

from ..._compat import iteritems
from ...exception_handling import mark_exception_frame_correction
from ...utils.python import wraps, get_argument_names
from .fixture_base import FixtureBase
from .utils import FixtureInfo, get_scope_by_name

_PARAM_INFO_ATTR_NAME = '__slash_parametrize__'


def parametrize(parameter_name, values):
    """Decorator to create multiple test cases out of a single function or module, where the cases vary by the value of ``parameter_name``,
    as iterated through ``values``.
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
        yield
    finally:
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
        values = list(values)

        if not isinstance(param_name, (list, tuple)):
            names = (param_name,)
        else:
            names = param_name

        values = _normalize_values(values, num_params=len(names))

        p = Parametrization(values=values, path='{}.{}'.format(self.path, param_name))
        for index, name in enumerate(names):
            if name in self._argument_name_set:
                params_dict = self._params
            else:
                params_dict = self._extra_params
            if len(names) > 1:
                params_dict[name] = p.as_transform(operator.itemgetter(index))
            else:
                params_dict[name] = p

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
        self.values = values
        if info is None:
            info = FixtureInfo(path=path)
        self.info = info
        self.scope = get_scope_by_name('test')
        self.transform = transform

    def get_value_by_index(self, index):
        return self.transform(self._compute_value(self.values[index]))

    def _compute_value(self, param):
        if isinstance(param, list):
            return [p.value for p in param]
        return param.value

    def is_parameter(self):
        return True

    def is_fixture(self):
        return False

    def get_value(self, kwargs, active_fixture):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        raise NotImplementedError()  # pragma: no cover

    def _resolve(self, store):
        return {}

    def as_transform(self, transform):
        returned = Parametrization(values=self.values, info=self.info, transform=transform, path=self.path)
        return returned


class ParametrizationValue(object):

    def __init__(self, label, value=NOTHING):
        super(ParametrizationValue, self).__init__()
        self._validate_label(label)
        self.label = label
        self.value = value

    def _validate_label(self, label):
        if isinstance(label, str) and not re.match(r'^[a-zA-Z_][0-9a-zA-Z_]{0,29}$', label):
            raise RuntimeError('Invalid label: {!r}'.format(label))

    def __rfloordiv__(self, other):
        assert self.value is NOTHING, 'Parameter already has a value'
        self.value = other
        return self


def _normalize_values(values, num_params=1):
    returned = []
    for index, value in enumerate(values):

        value = _normalize_single_value(value, default_label=index)
        if num_params > 1:
            if not isinstance(value.value, (tuple, list)):
                raise RuntimeError('Invalid parametrization value (expected sequence): {!r}'.format(value.value))
            if len(value.value) != num_params:
                raise RuntimeError('Invalid parametrization value (invalid length, expected {}): {!r}'.format(num_params, value.value))

        returned.append(value)
    return returned


def _normalize_single_value(value, default_label):
    if not isinstance(value, ParametrizationValue):
        value = ParametrizationValue(label=default_label, value=value)
    if value.value is NOTHING:
        raise mark_exception_frame_correction(
            RuntimeError('Parameter {} has no value defined!'.format(value.label)),
            +4)
    return value
