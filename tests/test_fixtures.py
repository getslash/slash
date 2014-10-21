import operator

import pytest

from slash._compat import itervalues, reduce


def test_fixtures(populated_suite, suite_test, defined_fixture):
    suite_test.add_fixture(defined_fixture)

    results = populated_suite.run()
    assert len(results[suite_test].data['fixtures']) == 1


def test_fixture_cleanup_at_end_of_suite(populated_suite):
    fixture = populated_suite.add_fixture()
    populated_suite[-1].add_fixture(fixture)
    fixture.add_cleanup()

    populated_suite.run()


def test_fixture_parameters(populated_suite, suite_test, defined_fixture):
    defined_fixture.parametrize()
    suite_test.add_fixture(defined_fixture)

    results = populated_suite.run()
    len(results.results_by_test_uuid[suite_test.uuid]) == reduce(
        operator.mul, itervalues(defined_fixture.params))


def test_fixture_dependency_chain(populated_suite, suite_test):
    fixture1 = populated_suite.add_fixture()
    fixture1.parametrize()
    fixture2 = populated_suite.add_fixture()
    fixture2.parametrize()
    fixture2.add_fixture(fixture1)
    suite_test.add_fixture(fixture2)

    populated_suite.run()


def test_fixture_dependency_both_directly_and_indirectly(populated_suite, suite_test):

    fixture1 = populated_suite.add_fixture()
    num_params1 = 2
    fixture1.parametrize(num_params=num_params1)

    fixture2 = populated_suite.add_fixture()
    num_params2 = 3
    fixture2.parametrize(num_params=num_params2)
    fixture2.add_fixture(fixture1)

    suite_test.add_fixture(fixture1)
    suite_test.add_fixture(fixture2)

    results = populated_suite.run()
    assert len(results.results_by_test_uuid[
               suite_test.uuid]) == num_params1 * num_params2



# Support fixtures

@pytest.fixture(params=["slashconf", "module"])
def defined_fixture(request, populated_suite, suite_test):
    if request.param == 'slashconf':
        return populated_suite.add_fixture()
    elif request.param == 'module':
        return suite_test.file.add_fixture()

    raise NotImplementedError()  # pragma: no cover
