import re


def test_cyclic_fixture_detection(suite, suite_test):
    fixture1 = suite.slashconf.add_fixture()
    fixture2 = suite.slashconf.add_fixture()
    fixture1.depend_on_fixture(fixture2)
    fixture2.depend_on_fixture(fixture1)

    suite_test.depend_on_fixture(fixture1)
    for test in suite:
        test.expect_deselect() # no test should start at all....

    summary = suite.run(expect_session_errors=True)
    assert not summary.session.results.global_result.is_success()
    assert re.search(r'yclic fixture dependency detected in \S+: {0} -> {1} -> {0}'.format(fixture1.name, fixture2.name),
                     summary.get_console_output())


def test_cyclic_fixture_detection_depend_on_self(suite, suite_test):
    fixture = suite.slashconf.add_fixture()
    fixture.depend_on_fixture(fixture)

    suite_test.depend_on_fixture(fixture)
    for test in suite:
        test.expect_deselect() # no test should start at all...

    summary = suite.run(expect_session_errors=True)
    assert not summary.session.results.global_result.is_success()
    assert re.search(r'yclic fixture dependency detected in \S+: {} depends on itself'.format(fixture.name),
                     summary.get_console_output())
