import pytest

def test_fixture_cleanup(populated_suite, suite_test):
    fixture = populated_suite.add_fixture()
    for i in range(3):
        fixture.add_cleanup()
    suite_test.add_fixture(fixture)
    populated_suite.run()
