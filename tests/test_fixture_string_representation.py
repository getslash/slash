import functools
import itertools
import random

import pytest
import slash
from slash._compat import StringIO
from slash.utils.iteration import iter_cartesian_dicts
from .utils.code_formatter import CodeFormatter


def test_safe_repr_parameters(fixture_store, parametrized_func, params, param_names):

    variations = list(
        fixture_store.iter_parametrization_variations(funcs=[parametrized_func]))

    cartesian_product = list(iter_cartesian_dicts(params))

    assert len(variations) == len(cartesian_product)
    variation_names = set(str(v.safe_repr) for v in variations)
    assert len(variation_names) == len(cartesian_product)
    assert variation_names == set(','.join('{0}={1}'.format(name, combination[name]) for name in sorted(param_names))
                                  for combination in cartesian_product)

def test_safe_repr_fixtures(fixture_store):

    first_param_values = [1, 2, 3]
    second_param_values = [4, 5, 6]

    @fixture_store.add_fixture
    @slash.fixture
    @slash.parametrize('value', first_param_values)
    def first_fixture(value):
        return value

    @fixture_store.add_fixture
    @slash.fixture
    @slash.parametrize('value', second_param_values)
    def second_fixture(value):
        return value

    def test_func(first_fixture, second_fixture):
        pass

    fixture_store.resolve()

    variations = list(
        fixture_store.iter_parametrization_variations(funcs=[test_func]))

    assert len(variations) == len(first_param_values) * len(second_param_values)

    assert set(str(variation.safe_repr) for variation in variations) == set(
        'first_fixture=first_fixture{0},second_fixture=second_fixture{1}'.format(i, j)
        for i, j in itertools.product(range(len(first_param_values)), range(len(second_param_values))))

@pytest.fixture
def parametrized_func(params, param_names):
    buff = StringIO()
    formatter = CodeFormatter(buff)
    formatter.writeln('def f({0}):'.format(', '.join(param_names)))
    with formatter.indented():
        formatter.writeln('pass')
    globs = {}
    exec(buff.getvalue(), globs)
    returned = globs['f']
    for param_name in param_names:
        returned = slash.parametrize(
            param_name, list(params[param_name]))(returned)
    return returned


@pytest.fixture(
    params=[
        sorted,
        functools.partial(sorted, reverse=True),
        functools.partial(sorted, key=lambda x: random.random()),
    ])
def param_names(request, params):
    sorter = request.param
    return sorter(params)


@pytest.fixture
def params():
    return {
        'a': [1, 2],
        'b': [4, 5],
        'c': [6, 7],
        'd': [8, 9],
    }


@pytest.fixture
def fixture_store():
    return slash.core.fixtures.fixture_store.FixtureStore()


@pytest.fixture(params=[str, repr])
def stringify(request):
    return request.param
