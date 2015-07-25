import copy

import pytest
import slash

from .utils import run_tests_assert_success
from .utils.suite_writer import Suite


def test_test_parametrization(test_type):
    suite = Suite()
    num_values1 = 3
    num_values2 = 5
    test = suite.add_test(type=test_type)
    test.add_parameter(num_values=num_values1)
    test.add_parameter(num_values=num_values2)
    summary = suite.run()
    assert len(summary.get_all_results_for_test(test)) == num_values1 * num_values2


def test_parameters_toggle():

    @slash.parameters.toggle('param')
    def test_example(param):
        _set('param', param)

    session = run_tests_assert_success(test_example)

    assert [False, True] == sorted(result.data['param'] for result in session.results)


def test_dict_parameter_values():

    values = [{'value': 1}, {'value': 2}]

    @slash.parametrize('param', copy.deepcopy(values))
    def test_example(param):
        _set('param', param)

    session = run_tests_assert_success(test_example)
    assert values == sorted((result.data['param'] for result in session.results), key=values.index)


def test_duplicate_parameters():

    values = ["a", "b", "a"]

    @slash.parametrize('param', copy.deepcopy(values))
    def test_example(param):
        _set('param', param)

    session = run_tests_assert_success(test_example)
    assert sorted(values) == sorted(result.data['param'] for result in session.results)



def test_before_after_parameters(cartesian):

    class Parameterized(slash.Test):

        @slash.parameters.iterate(a=cartesian.before_a.make_set())
        def before(self, a):
            _set("before_a", a)

        @slash.parameters.iterate(b=cartesian.b.make_set(), c=cartesian.c.make_set())
        def test(self, b, c):
            _set("b", b)
            _set("c", c)

        @slash.parameters.iterate(d=cartesian.after_d.make_set())
        def after(self, d):
            _set("after_d", d)

    session = run_tests_assert_success(Parameterized)
    assert len(session.results) == len(cartesian)
    cartesian.check(result.data for result in session.results)


@pytest.mark.parametrize('with_override', [True, False])
def test_before_parameters_inheritence(cartesian, with_override):

    class BaseTest(slash.Test):

        @slash.parameters.iterate(a=cartesian.before_1_a.make_set())
        def before(self, a):
            _set("before_1_a", a)

    class DerivedTest(BaseTest):

        @slash.parameters.iterate(a=cartesian.before_2_a.make_set(), b=cartesian.before_2_b.make_set())
        def before(self, a, b):
            if with_override:
                super(DerivedTest, self).before(a=a)
            else:
                super(DerivedTest, self).before()
            _set("before_2_a", a)
            _set("before_2_b", b)

        def test(self):
            pass

    session = run_tests_assert_success(DerivedTest)
    assert len(session.results) == len(cartesian)
    if with_override:
        cartesian.assign_all(
            source_name='before_2_a', target_name='before_1_a')
    cartesian.check(result.data for result in session.results)


def test_parametrization_tuples():

    @slash.parametrize(('a', 'b'), [(1, 2), (11, 22)])
    @slash.parametrize('c', [3, 33])
    def test_something(a, b, c):
        _set("params", (a, b, c))

    session = run_tests_assert_success(test_something)
    results = [result.data['params'] for result in session.results.iter_test_results()]
    expected = set([
        (1, 2, 3), (1, 2, 33), (11, 22, 3), (11, 22, 33)
        ])
    assert len(expected) == len(results)
    assert expected == set(results)

def test_parametrization_tuples_invalid_length():

    with pytest.raises(RuntimeError) as caught:
        @slash.parametrize(('a', 'b'), [(1, 2), (1,), (11, 22)])
        def test_something(a, b, c):
            pass
    assert 'Invalid parametrization value' in str(caught.value)
    assert 'invalid length' in str(caught.value)


def test_parametrization_tuples_invalid_type():

    with pytest.raises(RuntimeError) as caught:
        @slash.parametrize(('a', 'b'), [(1, 2), 200, (11, 22)])
        def test_something(a, b, c):
            pass
    assert 'Invalid parametrization value' in str(caught.value)
    assert 'expected sequence' in str(caught.value)



def _set(param, value):
    data = slash.session.results.current.data
    assert param not in data
    data[param] = value
