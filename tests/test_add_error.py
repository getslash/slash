import pytest


@pytest.mark.parametrize('failure_type', ['failure', 'error'])
def test_add_error_custom_exc_info(suite, suite_test, failure_type):

    for line in """
import sys
try:
    1/0
except ZeroDivisionError:
    exc_info = sys.exc_info()
    try:
        None.a = 2
    except AttributeError:
        slash.add_{0}(exc_info=exc_info)
    """.format(failure_type).strip().splitlines():
        suite_test.append_line(line)

    if failure_type == 'error':
        suite_test.expect_error()
    else:
        suite_test.expect_failure()
    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)

    if failure_type == 'error':
        [err] = result.get_errors()
    else:
        [err] = result.get_failures()
    assert err.exception_type is ZeroDivisionError

