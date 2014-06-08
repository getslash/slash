import slash

from .utils import run_tests_assert_success


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


def test_before_parameters_inheritence(cartesian):

    class BaseTest(slash.Test):

        @slash.parameters.iterate(a=cartesian.before_1_a.make_set())
        def before(self, a):
            _set("before_1", a)

    class DerivedTest(BaseTest):

        @slash.parameters.iterate(a=cartesian.before_2_a.make_set(), b=cartesian.before_2_b.make_set())
        def before(self, a, b):
            super(DerivedTest, self).before()
            _set("before_2_a", a)
            _set("before_2_b", b)

        def test(self):
            pass

    session = run_tests_assert_success(DerivedTest)
    assert len(session.results) == len(cartesian)


def _set(param, value):
    data = slash.session.results.current.data
    assert param not in data
    data[param] = value
