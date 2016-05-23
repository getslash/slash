from .utils import skip_on_py2, skip_on_pypy

@skip_on_py2
@skip_on_pypy
def test_fixture_alias(suite, suite_test, get_fixture_location):

    fixture = get_fixture_location(suite_test).add_fixture()
    suite_test.depend_on_fixture(fixture, alias=True)

    suite.run()

@skip_on_py2
@skip_on_pypy
def test_nested_fixture_alias(suite, suite_test, get_fixture_location):

    fixture = get_fixture_location(suite_test).add_fixture()
    fixture2 = get_fixture_location(suite_test).add_fixture()
    fixture.depend_on_fixture(fixture2, alias=True)
    suite_test.depend_on_fixture(fixture)

    suite.run()
