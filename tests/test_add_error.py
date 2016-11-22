from uuid import uuid4
import pytest


@pytest.mark.parametrize('failure_type', ['failure', 'error'])
@pytest.mark.parametrize('use_custom_message', [True, False])
def test_add_error_custom_exc_info(suite, suite_test, failure_type, use_custom_message):
    message = str(uuid4())

    if use_custom_message:
        add_error_args = '{!r}, '.format(message)
    else:
        add_error_args = ''

    add_error_args += 'exc_info=exc_info'

    code = """
import sys
try:
    1/0
except ZeroDivisionError:
    exc_info = sys.exc_info()
    try:
        None.a = 2
    except AttributeError:
        slash.add_{0}({1})
    """.format(failure_type, add_error_args)

    for line in code.strip().splitlines():
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

    assert err.has_custom_message() == use_custom_message
    if use_custom_message:
        assert err.message == message
    assert err.exception_type is ZeroDivisionError
    assert err.traceback.frames

