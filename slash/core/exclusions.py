from ..ctx import context
from ..exceptions import UnknownFixtures
from .fixtures.parameters import Parametrization
from . import markers


def exclude(names, values):
    """
    Excludes a specific parametrization of a test from running

    :param name: can receive either a name of a parameter for this test, or a name of a fixture parameter
    :param values: must be a list of values to exclude for the given parameter
    """
    if not isinstance(values, (tuple, list)):
        raise RuntimeError('Invalid exclude values specified: must be a sequence, got {!r}'.format(values))
    if not isinstance(names, (tuple, list)):
        names = (names,)
        values = [(value,) for value in values]
    elif not isinstance(values, (tuple, list)) or any(not isinstance(item, tuple) for item in values):
        raise RuntimeError('Invalid exclude values specified for {}: {!r}'.format(', '.join(names), values))

    values = [tuple(value_set) for value_set in values]
    return markers.exclude_marker((names, values))

def is_excluded(test):
    test_func = test.get_test_function()
    exclusions = markers.exclude_marker.get_value(test_func, default=None)
    if not exclusions:
        return False
    exclusions = dict(exclusions)
    for parameter_names, value_sets in exclusions.items():
        params = []
        values = []
        for parameter_name in parameter_names:
            param = context.session.fixture_store.resolve_name(parameter_name, start_point=test_func, namespace=test.get_fixture_namespace())
            if not isinstance(param, Parametrization):
                raise UnknownFixtures('{!r} is not a parameter, and therefore cannot be the base for value exclusions'.format(parameter_name))
            params.append(param)


            try:
                param_index = test.__slash__.variation.param_value_indices[param.info.id] #pylint: disable=no-member
            except LookupError:
                raise UnknownFixtures('{!r} cannot be excluded for {!r}'.format(parameter_name, test))
            value = param.get_value_by_index(param_index)
            values.append(value)

        if tuple(values) in value_sets:
            return True
    return False
