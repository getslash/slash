import operator
import re
from contextlib import contextmanager
from sentinels import NOTHING
from ...conf import config
from ..._compat import iteritems
from ...exceptions import ParameterException
from ...exception_handling import mark_exception_frame_correction
from ...utils.python import wraps, get_argument_names
from .fixture_base import FixtureBase
from .utils import FixtureInfo, get_scope_by_name
import logbook
logger = logbook.Logger(__name__)

_PARAM_INFO_ATTR_NAME = '__slash_parametrize__'


def parametrize(parameter_name, values, compute=None):
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

        params.add_options(parameter_name, values, compute)
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

    def add_options(self, param_name, values, compute):
        if param_name in self._params:
            raise ParameterException('{!r} already parametrized for {}'.format(
            param_name, self.path))
        values = list(values)

        if not isinstance(param_name, (list, tuple)):
            names = (param_name,)
        else:
            names = param_name

        values = _normalize_values(values, num_params=len(names), compute=compute)

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

    def get_value_by_index(self, index, compute=False):
        return self.transform(self._compute_value(self.values[index], compute=compute))

    def _compute_value(self, param, compute=False):
        if isinstance(param, list):
            return [p.compute_value() for p in param] if compute else [p.get_value() for p in param]
        return param.compute_value() if compute else param.get_value()

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

    def __init__(self, label, value=NOTHING, compute=None):
        super(ParametrizationValue, self).__init__()
        self._validate_label(label)
        self.label = label
        self._value = value
        if compute is not None:
            assert callable(compute)
        self._compute = compute

    def compute_value(self):
        if self._compute is not None:
            self._value = self._compute()
            if config.root.log.show_raw_param_values:
                logger.info("Value of parameter {} changed to {}", self.label, self._value)
        return self._value

    def get_value(self):
        return self._value

    def get_compute(self):
        return self._compute

    def _validate_label(self, label):
        if isinstance(label, str) and not re.match(r'^[a-zA-Z_][0-9a-zA-Z_]{0,29}$', label):
            raise RuntimeError('Invalid label: {!r}'.format(label))

    def __rfloordiv__(self, other):
        assert self._value is NOTHING, 'Parameter already has a value'
        self._value = other
        return self


def _normalize_values(values, num_params=1, compute=None):
    returned = []
    for index, value in enumerate(values):
        param = _normalize_single_value(value, default_label=index, compute=compute)
        if num_params > 1 and param.get_compute() is None:
            if not isinstance(param.get_value(), (tuple, list)):
                raise RuntimeError('Invalid parametrization value (expected sequence): {!r}'.format(param.get_value()))
            if len(param.get_value()) != num_params:
                raise RuntimeError('Invalid parametrization value (invalid length, expected {}): {!r}'.format(num_params, param.get_value()))

        returned.append(param)
    return returned


def _normalize_single_value(value, default_label, compute=None):
    if isinstance(value, ParametrizationValue):
        compute = value.get_compute()
    else:
        value = ParametrizationValue(label=default_label, value=value, compute=compute)
    if compute is None and value.get_value() is NOTHING:
        raise mark_exception_frame_correction(
            RuntimeError('Parameter {} has no value defined!'.format(value.label)),
            +4)
    if compute is not None and value.get_value() is not NOTHING:
        raise mark_exception_frame_correction(
            RuntimeError('Parameter {} has both value and compute defined!'.format(value.label)),
            +4)
    return value
