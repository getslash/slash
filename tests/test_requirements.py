import pytest
import slash
from slash.loader import Loader

from .utils import make_runnable_tests


def test_requirements_mismatch_session_success(suite, suite_test):
    suite_test.add_decorator('slash.requires(False)')
    suite_test.expect_skip()
    summary = suite.run()
    assert summary.session.results.is_success(allow_skips=True)


@pytest.mark.parametrize('requirement_fullfilled', [True, False])
@pytest.mark.parametrize('use_message', [True, False])
@pytest.mark.parametrize('use_fixtures', [True, False])
def test_requirements(suite, suite_test, requirement_fullfilled, use_fixtures, use_message):

    suite_test.add_decorator('slash.requires(lambda: {0})'.format(requirement_fullfilled))
    if not requirement_fullfilled:
        suite_test.expect_skip()

    if use_fixtures:
        suite_test.depend_on_fixture(
            suite.slashconf.add_fixture())
    results = suite.run()
    if requirement_fullfilled:
        assert results[suite_test].is_success()
    else:
        assert not results[suite_test].is_started()
        assert results[suite_test].is_skip()


def test_requirements_on_class():

    def req1():
        pass

    def req2():
        pass

    @slash.requires(req1)
    class Test(slash.Test):

        @slash.requires(req2)
        def test_something(self):
            pass

    with slash.Session():
        [test] = make_runnable_tests(Test)

    assert [r._req for r in test.get_requirements()] == [req1, req2]
