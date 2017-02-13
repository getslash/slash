# pylint: disable=unused-variable, unused-argument, redefined-outer-name
import collections
import copy
from uuid import uuid4

import gossip
import pytest
import slash
from munch import Munch

from .utils import make_runnable_tests


def test_variation_info_without_params_is_none(results):
    assert len(results.test_no_params) == 1
    for res in results.test_no_params:
        assert res.test_metadata.variation.values == {}


def test_variation_info_single_value_id_none(results):
    assert len(results.test_single_param_fixture) == 1
    for res in results.test_single_param_fixture:
        assert res.test_metadata.variation.id is not None
        assert res.test_metadata.variation.values == {}
        assert 'fixture' not in res.data['captured_values']

def test_unique_variation_ids(results):
    all_results = [res for result_set in results.values() for res in result_set]
    ids = {_freeze(res.test_metadata.variation.id) for res in all_results}
    assert len(ids) == len(all_results) - 1 # we subtract one because no params and a single fixture have the same id
    assert None not in ids


def test_parametrization_info_availabe_on_test_start(checkpoint):
    param_value = str(uuid4())

    @gossip.register('slash.test_start')
    def test_start_hook():
        assert slash.context.test.__slash__.variation.values['param'] == param_value
        assert 'fixture' not in slash.context.test.__slash__.variation.values
        checkpoint()

    @slash.parametrize('param', [param_value])
    def test_something(param, fixture):
        pass

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.fixture
        def fixture():
            pass

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))

    assert s.results.is_success(allow_skips=False)
    assert checkpoint.called



def test_parametrization_info_values_include_nested_fixture_values():

    value1 = str(uuid4())
    value2 = str(uuid4())

    @gossip.register('slash.test_start')
    def test_start_hook():
        slash.context.result.data['variation_values'] = slash.context.test.__slash__.variation.values.copy()

    @slash.parametrize('param', ['some_value'])
    def test_something(param, some_fixture):
        pass

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.fixture
        @slash.parametrize('value', [value1, value2])
        def some_fixture(value):
            pass

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))

    assert s.results.is_success(allow_skips=False)
    all_values = []
    for result in s.results.iter_test_results():
        values = result.data['variation_values']
        all_values.append(values['some_fixture.value'])

    assert len(all_values) == 2
    assert set(all_values) == {value1, value2}


def test_variation_identification():
    value1 = str(uuid4())
    value2 = str(uuid4())

    @gossip.register('slash.test_start')
    def test_start_hook():
        variation = slash.context.test.__slash__.variation
        slash.context.result.data['variation_info'] = {
            'id': variation.id.copy(),
            'values': variation.values.copy(),
        }


    @slash.parametrize('param', ['some_value'])
    def test_something(param, some_fixture):
        pass

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.fixture
        @slash.parametrize('value', [value1])
        def some_fixture(value):
            return value2

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))

    assert s.results.is_success(allow_skips=False)
    [info] = [result.data['variation_info'] for result in s.results.iter_test_results()]
    assert info['id']['param'] == 0
    assert info['values']['param'] == 'some_value'
    assert info['id']['some_fixture.value'] == 0
    assert 'some_fixture' not in info['values']
    assert info['values']['some_fixture.value'] == value1





def _freeze(dictionary):
    return frozenset(dictionary.items())

def test_variation_tuples(results):
    [res] = results.test_parametrization_tuple
    values = res.data['captured_values']
    assert values['x'] == 1
    assert values['y'] == 2

def test_nested_fixture_ids(results):
    ids = {res.data['captured_values']['outer_fixture.outer_param'] for res in results.test_nested_fixture}
    assert ids == {666}
    for res in results.test_nested_fixture:
        assert 'outer_fixture' not in res.data['captured_values']

def test_fixture_and_toggle(results):
    assert len(results.test_fixture_and_toggle) == 2


@pytest.fixture
def results():

    tests = []
    def include(f):
        tests.append(f)
        return f

    @include
    def test_no_params():
        pass

    @include
    def test_single_param_fixture(fixture):
        _capture_arguments()

    @include
    def test_nested_fixture(outer_fixture):
        _capture_arguments()

    @include
    @slash.parametrize(('x', 'y'), [(1, 2)])
    def test_parametrization_tuple(x, y):
        _capture_arguments()

    @include
    @slash.parameters.toggle('toggle')
    def test_fixture_and_toggle(fixture, toggle):
        _capture_arguments()

    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.fixture
        def fixture():
            return _object1

        @s.fixture_store.add_fixture
        @slash.fixture
        @slash.parametrize('x', [1, 2, 3])
        def inner_fixture(x):
            return 'inner{}'.format(x)

        @s.fixture_store.add_fixture
        @slash.fixture
        @slash.parametrize('outer_param', [666])
        def outer_fixture(inner_fixture, outer_param):
            return 'outer_{}'.format(inner_fixture)

        s.fixture_store.resolve()

        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(tests))
    assert s.results.is_success(allow_skips=False)

    returned = collections.defaultdict(list)
    for res in s.results.iter_test_results():
        returned[res.test_metadata.function_name].append(res)
    return Munch(returned)

# helpers ################################################################################

_object1 = object()


def _capture_arguments():
    values = copy.copy(slash.context.result.test_metadata.variation.values)
    slash.context.result.data['captured_values'] = values
