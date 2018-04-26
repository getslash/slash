# pylint: disable=unused-variable, unused-argument
import slash
import pytest

from .utils import resolve_and_run

def test_fixture_exclusion():

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.parametrize('param', [1, 2])
        @slash.fixture
        def fixture(param):
            return param * 10

        @slash.exclude('fixture.param', [2])
        def test_something(fixture):
            slash.context.result.data['value'] = fixture

        results = resolve_and_run(test_something)
    assert len(results) == 2
    assert results[0].is_success()
    assert results[0].data['value'] == 10
    assert results[1].is_skip()
    assert not results[1].is_started()


def test_fixture_exclusion_nested(suite, suite_test):

    fixture = suite.slashconf.add_fixture()
    param = fixture.add_parameter()
    suite_test.depend_on_fixture(fixture)

    param_value = param.values[0]

    suite_test.add_decorator('slash.exclude("{fixture_name}.{param_name}", {values})'.format(
        fixture_name=fixture.name,
        param_name=param.name,
        values=[param_value],
    ))
    suite_test.exclude_param_value(param.name, param_value)
    suite.run()


def test_fixture_exclusion_multiple():

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.parametrize('param', [1, 2])
        @slash.fixture
        def fixture1(param):
            return param * 10

        @s.fixture_store.add_fixture
        @slash.parametrize('param', [3, 4])
        @slash.fixture
        def fixture2(param):
            return param * 10


        @slash.exclude(('fixture1.param', 'fixture2.param'), [(2, 3)])
        def test_something(fixture1, fixture2):
            slash.context.result.data['values'] = fixture1, fixture2

        results = resolve_and_run(test_something)
    assert len(results) == 4

    value_pairs = [
        result.data.get('values')
        for result in results
    ]

    for result, value_pair in zip(results, value_pairs):
        if value_pair is None:
            assert not result.is_started()
        else:
            assert result.is_success()

    assert value_pairs == [(10, 30), (10, 40), None, (20, 40)]


@pytest.mark.parametrize('names,values', [
    (['x'], 1),
    (['x'], [1]),
])
def test_invalid_exclude_patterns(names, values):
    with pytest.raises(RuntimeError) as caught:
        slash.exclude(names, values)
    assert 'Invalid exclude values' in str(caught.value)

@pytest.mark.parametrize('names,values', [
    ('x', [1]),
    (['x'], [(1,)]),
])
def test_valid_exclude_patterns(names, values):
    slash.exclude(names, values)
