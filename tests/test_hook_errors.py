import itertools

import gossip
import pytest
import slash

from .utils import CustomException, run_tests_in_session


def test_scope_management_with_hook_error_test_start(suite, suite_test):
    assert len(suite.files) > 1
    assert len(suite) > 1

    @gossip.register('slash.test_start')
    def hook():
        raise CustomException()

    for test in suite:
        test.expect_error()
    summary = suite.run()
    for res in summary.session.results.iter_test_results():
        [err] = res.get_errors()
        assert err.exception_type is CustomException

def test_scope_management_with_hook_error_test_end():
    """test_end errors are fatal, so the session abruptly stops. We just make sure we get the exception and that at least one test runs"""
    events = []

    gossip.register('slash.test_end')(CustomException.do_raise)

    @slash.parametrize('param', range(10))
    def test_something(param):
        events.append('test is running!')

    with slash.Session() as session:
        tests = slash.loader.Loader().get_runnables(test_something)
        assert tests
        with pytest.raises(CustomException) as caught:
            run_tests_in_session(tests, session=session)

    assert len(events) == 1
    assert len(tests) > 1
