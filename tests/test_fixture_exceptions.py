import pytest


@pytest.mark.parametrize('scope', ['test', 'session'])
@pytest.mark.parametrize('use_skip', [True, False])
def test_exceptions_in_fixture(suite, suite_test, scope, use_skip):
    second_test = suite_test.file.add_function_test()

    fixture = suite_test.file.add_fixture(scope=scope)
    suite_test.depend_on_fixture(fixture)
    second_test.depend_on_fixture(fixture)

    if use_skip:
        fixture.append_line('slash.skip_test()')
    else:
        fixture.append_line('assert False')

    for test in suite_test, second_test:
        if use_skip:
            test.expect_skip()
        else:
            test.expect_failure()

    suite.run()
