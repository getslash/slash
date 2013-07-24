import itertools
from ._compat import iteritems

def iterate(**parameters_and_values):
    """
    For each PARAM=OPTIONS passed, will cause the
    decorated test method to be actually run several times
    upon execution, one for each possible parameter
    """
    def _decorator(func):
        specs = _get_or_create_parameter_specs(func)
        for parameter_name, options in iteritems(parameters_and_values):
            specs.setdefault(parameter_name, []).extend(options)
        return func
    return _decorator

def _get_or_create_parameter_specs(func):
    returned = _get_parameter_specs(func)
    if returned is None:
        returned = func.__slash_parameters__ = {}
    return returned

def _get_parameter_specs(func):
    return getattr(func, "__slash_parameters__", None)

def iterate_kwargs_options(func):
    specs = _get_parameter_specs(func)
    if specs is None:
        yield {}
        return
    specs = list(iteritems(specs))
    names = [first for first, second in specs]
    values = [second for first, second in specs]
    for combination in itertools.product(*values): # pylint: disable=W0142
        yield dict(zip(names, combination))
