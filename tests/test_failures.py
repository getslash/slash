import pytest

import slash
from .utils.suite_writer import Suite

def test_failures_call_test_failure_hook(request, suite, suite_test, checkpoint):
    suite_test.append_line('assert False')

    @slash.hooks.test_failure.register
    def callback(*_, **__):
        checkpoint()

    suite_test.expect_failure()
    summary = suite.run()
    assert checkpoint.called_count == 1

@pytest.mark.parametrize('error_adder', ['add_error', 'add_failure'])
def test_adding_errors(error_adder, test_type):

    suite = Suite()
    test = suite.add_test(type=test_type)

    for i in range(2):
        test.append_line('slash.{0}("msg{1}")'.format(error_adder, i))
    test.append_line('slash.{0}(object())'.format(error_adder))

    if error_adder == 'add_error':
        test.expect_error()
    else:
        test.expect_failure()

    results = suite.run().session.results

    [test_result] = results.iter_test_results()

    objs = test_result.get_errors() if error_adder == 'add_error' else test_result.get_failures()
    assert len(objs) == 3

    assert 'msg0' in objs[0].message
    assert 'msg1' in objs[1].message
    assert '<object object at 0x' in objs[2].message


def test_add_failure_error_object_marked_as_failure():

    with slash.Session() as s:
        with s.get_started_context():
            slash.add_failure('msg')
        [failure] = slash.context.result.get_failures()
    assert failure.is_failure()


def test_manual_add_error_preserves_traceback(suite, suite_test):
    suite_test.append_line('slash.add_error("error here")')
    suite_test.expect_error()
    summary = suite.run()

    [result] = summary.get_all_results_for_test(suite_test)
    [err] = result.get_errors()

    assert err.traceback is not None

def test_manual_add_error_requires_argument(suite, suite_test):
    suite_test.append_line('slash.add_error()')
    suite_test.expect_error()
    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    [err] = result.get_errors()
    assert 'RuntimeError' in str(err)
    assert 'add_error() must be called' in str(err)
