from contextlib import contextmanager

from ..._compat import itervalues, iteritems
from .fixture_base import FixtureBase
from .utils import FixtureInfo, get_scope_by_name
from ...utils.python import wraps

_PARAM_INFO_ATTR_NAME = '__slash_parametrize__'


def parametrize(parameter_name, values):
    def decorator(func):

        params = getattr(func, _PARAM_INFO_ATTR_NAME, None)
        if params is None:
            params = ParameterizationInfo()

            @wraps(func, preserve=['__slash_fixture__'])
            def new_func(*args, **kwargs):
                for fixture in params.get_parametrization_fixtures():
                    if fixture.name not in kwargs:
                        assert _current_bindings is not None, 'Not called in parametrization context'
                        if fixture.info.id in _current_bindings:
                            kwargs[fixture.name] = _current_bindings[
                                fixture.info.id]
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


_current_bindings = None


@contextmanager
def bound_parametrizations_context(parameter_ids_to_values):
    global _current_bindings
    assert _current_bindings is None
    _current_bindings = parameter_ids_to_values
    try:
        yield
    finally:
        _current_bindings = None


def get_parametrization_fixtures(func):
    param_info = getattr(func, _PARAM_INFO_ATTR_NAME, None)
    if param_info is None:
        return []
    return param_info.get_parametrization_fixtures()


class ParameterizationInfo(object):

    def __init__(self):
        super(ParameterizationInfo, self).__init__()
        self._params = {}
        self._fixtures = {}

    def add_options(self, param_name, options):
        assert param_name not in self._params

        self._params[param_name] = list(options)
        self._fixtures[param_name] = Parametrization(
            param_name, self._params[param_name])

    def get_parametrization_fixtures(self):
        return list(itervalues(self._fixtures))


class Parametrization(FixtureBase):

    def __init__(self, name, values):
        super(Parametrization, self).__init__()
        self.name = name
        self.info = FixtureInfo(name=name)
        self.scope = get_scope_by_name('test')
        self.values = list(values)

    def get_value(self, kwargs):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        return self.values

    def _resolve(self, store):
        return {}
