import pytest
from .utils import skip_on_py2, skip_on_pypy

@skip_on_py2
@skip_on_pypy
@pytest.mark.parametrize('alias_with_attribute', [True, False])
def test_fixture_annotations(suite, suite_test, get_fixture_location, alias_with_attribute):

    fixture = get_fixture_location(suite_test).add_fixture()
    suite_test.depend_on_fixture(fixture, alias=True, alias_with_attribute=alias_with_attribute)

    suite.run()

@skip_on_py2
@skip_on_pypy
@pytest.mark.parametrize('alias_with_attribute', [True, False])
def test_nested_fixture_annotations(suite, suite_test, get_fixture_location, alias_with_attribute):

    fixture = get_fixture_location(suite_test).add_fixture()
    fixture2 = get_fixture_location(suite_test).add_fixture()
    fixture.depend_on_fixture(fixture2, alias=True, alias_with_attribute=alias_with_attribute)
    suite_test.depend_on_fixture(fixture)

    suite.run()
