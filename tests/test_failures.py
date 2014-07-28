import pytest

@pytest.mark.parametrize('error_adder', ['add_error', 'add_failure'])
def test_adding_errors(error_adder, suite):

    test = suite.add_test()

    for i in range(2):
        test.inject_line('slash.{0}("msg{1}")'.format(error_adder, i))
    test.inject_line('slash.{0}(object())'.format(error_adder))

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
