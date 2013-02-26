def run_tests(iterable):
    """
    Runs tests from an iterable using the current suite
    """
    for test in iterable:
        test.run()

