from .utils.suite_writer import Suite



def test_nofixtures(test_type):
    suite = Suite()
    test = suite.add_test(type=test_type)
    test.add_parameter_string('a=2, b=3')
    test.append_line('assert a == 2')
    test.append_line('assert b == 3')
    test.add_decorator('slash.nofixtures')
    assert suite.run().ok()
