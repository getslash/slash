import pytest
import slash

from .utils import run_tests_assert_success


def test_test_parametrization(suite, test_factory):
    num_params1 = 3
    num_params2 = 5
    test = test_factory(suite)
    test.parametrize(num_params=num_params1)
    test.parametrize(num_params=num_params2)
    results = suite.run()
    assert len(
        results.results_by_test_uuid[test.uuid]) == num_params1 * num_params2


def test_parameters_toggle(suite, test_factory):

    @slash.parameters.toggle('param')
    def test_example(param):
        _set('param', param)

    session = run_tests_assert_success(test_example)

    assert [False, True] == sorted(result.data['param'] for result in session.results)


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


def _set(param, value):
    data = slash.session.results.current.data
    assert param not in data
    data[param] = value
