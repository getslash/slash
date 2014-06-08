import itertools
from contextlib import contextmanager

import logbook

from ._compat import ExitStack, iteritems, map

_logger = logbook.Logger(__name__)


def iterate(**parameters_and_values):
    """
    For each PARAM=OPTIONS passed, will cause the
    decorated test method to be actually run several times
    upon execution, one for each possible parameter
    """
    def _decorator(func):

        returned = func

        params = getattr(func, "__slash_parameters__", None)
        if params is None:
            params = Parameters()

            def new_func(*args, **kwargs):
                kwargs = params.get_kwargs(kwargs)
                return func(*args, **kwargs)
            new_func.__slash_parameters__ = params
            returned = new_func

        for parameter_name, values in iteritems(parameters_and_values):
            params.multiply(parameter_name, values)

        return returned
    return _decorator

_prefixes = map("{0}.".format, itertools.count())


class Parameters(object):

    def __init__(self):
        super(Parameters, self).__init__()
        self.prefix = next(_prefixes)
        self.params = {}

    def multiply(self, name, values):
        self.params[name] = list(values)

    def get_kwargs(self, kwargs):
        new_kwargs = kwargs.copy()
        for parameter_name in self.params:
            if parameter_name in new_kwargs:
                continue
            new_kwargs[parameter_name] = _current_parameter_set[
                self.prefix + parameter_name]
        return new_kwargs

    def iter_parameter_combinations(self):
        names = []
        value_sets = []
        for name in self.params:
            names.append(name)
            value_sets.append(self.params[name])
        for combination in itertools.product(*value_sets):  # pylint: disable=W0142
            yield dict((QualifiedParameterName(self.prefix, name), value) for name, value in zip(names, combination))

class QualifiedParameterName(object):
    def __init__(self, prefix, name):
        super(QualifiedParameterName, self).__init__()
        self.name = name
        self.fullname = prefix + name

    def __hash__(self):
        return hash(self.fullname)

    def __eq__(self, other):
        if isinstance(other, QualifiedParameterName):
            other = other.fullname
        return self.fullname == other

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return self.name

_current_parameter_set = {}


@contextmanager
def set_parameter_values_context(combinations):
    with ExitStack() as stack:
        for combination in combinations:
            for param_name, param_value in iteritems(combination):
                _current_parameter_set[param_name.fullname] = param_value
                stack.callback(_current_parameter_set.pop, param_name.fullname)
        yield


def iter_parameter_combinations(func):
    specs = getattr(func, "__slash_parameters__", None)
    if specs is None:
        yield {}
        return
    for x in specs.iter_parameter_combinations():
        yield x


def iter_inherited_method_parameter_combinations(cls, func_name):
    return _iter_inherited_method_parameter_combinations(cls.__mro__, func_name)


def _iter_inherited_method_parameter_combinations(mro, func_name):
    if not mro:
        yield {}
        return

    for base_combination in _iter_inherited_method_parameter_combinations(mro[1:], func_name):
        yielded = False
        for combination in iter_parameter_combinations(mro[0].__dict__.get(func_name, None)):
            yielded = True
            yield _overlay(base_combination, combination)
        if not yielded:
            yield base_combination

def _overlay(base_dict, overlay):
    returned = base_dict.copy()
    returned.update(overlay)
    return returned
