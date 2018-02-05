from . import markers

from ..ctx import context

from .fixtures.parameters import Parametrization
from ..exceptions import UnknownFixtures


def exclude(name, values):
    """
    Excludes a specific parametrization of a test from running

    :param name: can receive either a name of a parameter for this test, or a name of a fixture parameter
    :param values: must be a list of values to exclude for the given parameter
    """
    return markers.exclude_marker((name, values))

def is_excluded(test):
    test_func = test.get_test_function()
    exclusions = markers.exclude_marker.get_value(test_func, default=None)
    if not exclusions:
        return False
    exclusions = dict(exclusions)
    for parameter_name, values in exclusions.items():
        param = context.session.fixture_store.resolve_name(parameter_name, start_point=test_func, namespace=test.get_fixture_namespace())
        if not isinstance(param, Parametrization):
            raise UnknownFixtures('{!r} is not a parameter, and therefore cannot be the base for value exclusions'.format(parameter_name))
        try:
            param_index = test.__slash__.variation.param_value_indices[param.info.id] #pylint: disable=no-member
        except LookupError:
            raise UnknownFixtures('{!r} cannot be excluded for {!r}'.format(parameter_name, test))
        value = param.get_value_by_index(param_index)
        if value in values:
            return True
    return False
