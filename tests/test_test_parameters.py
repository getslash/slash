import slash

from .utils import run_tests_assert_success


def test_before_after_parameters(cartesian):

    def _set(param, value):
        data = slash.session.results.current.data
        assert param not in data
        data[param] = value

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
