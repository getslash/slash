from .utils.suite_writer import Suite

def test_default_factory_balanced_between_methods_and_functions():
    suite = Suite()
    assert suite.num_method_tests == suite.num_function_tests == 0
    suite.add_test()
    suite.add_test()
    assert suite.num_method_tests == suite.num_function_tests == 1
