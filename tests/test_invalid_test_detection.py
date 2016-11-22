from slash.exceptions import InvalidTest

def test_accidental_generator(suite, suite_test):
    suite_test.append_line('yield')
    suite_test.expect_error()
    res = suite.run()[suite_test]
    [err] = res.get_errors()
    assert err.exception_type is InvalidTest
    assert 'is a generator' in err.message
