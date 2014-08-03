import pytest


def test_fixtures(populated_suite, suite_test, defined_fixture):
    suite_test.add_fixture(defined_fixture)

    results = populated_suite.run()
    assert len(results[suite_test].data['fixtures']) == 1


def test_fixture_parameters(populated_suite, suite_test, defined_fixture):
    params = defined_fixture.parametrize()
    suite_test.add_fixture(defined_fixture)

    results = populated_suite.run()
    len(results.results_by_test_uuid[suite_test.uuid]) == len(params)


def test_dependent_fixtures():
    pytest.skip('!')

    fixture = populated_suite.add_fixture()
    fixture.parametrize()
    defined_fixture.add_fixture(fixture)
    defined_fixture.parametrize()

    populated_suite.run()


def test_dependent_fixtures_parameters():
    pytest.skip('!')


@pytest.fixture(params=["slashconf", "module"])
def defined_fixture(request, populated_suite, suite_test):
    if request.param == 'slashconf':
        return populated_suite.add_fixture()
    elif request.param == 'module':
        return suite_test.file.add_fixture()

    raise NotImplementedError()  # pragma: no cover
