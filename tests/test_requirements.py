import pytest
import slash
from slash.loader import Loader

@pytest.mark.parametrize('requirement_fullfilled', [True, False])
@pytest.mark.parametrize('use_message', [True, False])
@pytest.mark.parametrize('use_fixtures', [True, False])
def test_requirements(populated_suite, suite_test, requirement_fullfilled, use_fixtures, use_message):
    suite_test.add_requirement(requirement_fullfilled, use_message=use_message)
    if use_fixtures:
        suite_test.add_fixture(
            populated_suite.add_fixture())
    results = populated_suite.run()
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
        [test] = Loader().get_runnables(Test)

    assert [r._req for r in test.get_requirements()] == [req1, req2]
