from contextlib import contextmanager

from ..._compat import itervalues, iteritems, string_types
from .fixture_base import FixtureBase
from .utils import FixtureInfo, get_scope_by_name
from ...utils.python import wraps

_PARAM_INFO_ATTR_NAME = '__slash_parametrize__'


def parametrize(parameter_name, values):
    """Decorator to create multiple test cases out of a single function or module, where the cases vary by the value of ``parameter_name``, as iterated through ``values``.
    """

    def decorator(func):

        params = getattr(func, _PARAM_INFO_ATTR_NAME, None)
        if params is None:
            params = ParameterizationInfo()

            @wraps(func, preserve=['__slash_fixture__'])
            def new_func(*args, **kwargs):
                # for better debugging. _current_variation gets set to None on context exit
                variation = _current_variation
                for param in params.get_parametrization_fixtures():
                    if not param.is_in_kwargs(kwargs):
                        assert variation is not None, 'Not called in parametrization context'
                        if variation.has_value_for_parameter(param.info.id):
                            param.assign_to_kwargs_from_variation(kwargs, variation)

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
def bound_parametrizations_context(variation):
    global _current_variation  # pylint: disable=global-statement
    assert _current_variation is None
    _current_variation = variation
    try:
        yield
    finally:
        _current_variation = None


def get_parametrizations(func):
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
        self.values = list(values)
        if isinstance(name, string_types):
            self.names = (name,)
            self.unpack = False
        else:
            self.names = name
            self.unpack = True
            for option in self.values:
                if not isinstance(option, (tuple, list)):
                    raise RuntimeError('Invalid parametrization value (expected sequence): {0!r}'.format(option))
                if len(option) != len(self.names):
                    raise RuntimeError('Invalid parametrization value (invalid length): {0!r}'.format(option))
        self.info = FixtureInfo()
        self.scope = get_scope_by_name('test')

    def get_value(self, kwargs, active_fixture):
        raise NotImplementedError()  # pragma: no cover

    def get_variations(self):
        raise NotImplementedError() # pragma: no cover

    def _resolve(self, store):
        return {}

    def is_in_kwargs(self, kwargs):
        return all(name in kwargs for name in self.names)

    def assign_to_kwargs_from_variation(self, kwargs, variation):
        value = variation.get_param_value(self.info.id)
        if self.unpack:
            for name, value in zip(self.names, value):
                kwargs[name] = value
        else:
            assert len(self.names) == 1
            kwargs[self.names[0]] = value
