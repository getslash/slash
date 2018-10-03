import gossip
import slash

from .utils import CustomException, run_tests_in_session


def test_scope_management_with_hook_error_test_start(suite, suite_test):  # pylint: disable=unused-argument
    assert len(suite.files) > 1
    assert len(suite) > 1

    @gossip.register('slash.test_start')
    def hook():  # pylint: disable=unused-variable
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

    num_tests = 10

    @slash.parametrize('param', range(num_tests))  # pylint: disable=unused-argument
    def test_something(param):  # pylint: disable=unused-argument
        events.append('test is running!')

    with slash.Session() as session:
        tests = slash.loader.Loader().get_runnables(test_something)
        assert tests
        run_tests_in_session(test_something, session=session)

    for result in session.results.iter_test_results():
        assert len(result.get_errors()) == 1
        assert result.get_errors()[0].exception_type is CustomException

    assert len(events) == num_tests
    assert len(session.results) == num_tests
