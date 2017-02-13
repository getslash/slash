import pytest


def test_fixture_cleanup(suite, suite_test):
    fixture = suite.slashconf.add_fixture()
    for _ in range(3):
        fixture.add_cleanup()
    suite_test.depend_on_fixture(fixture)
    suite.run()


@pytest.mark.parametrize('scope', ['session', 'module'])
def test_fixture_autouse_with_scoping(suite, suite_test, scope):

    fixture = suite_test.file.add_fixture(autouse=True, scope=scope)
    fixture.add_cleanup()

    summary = suite.run()  # pylint: disable=unused-variable
