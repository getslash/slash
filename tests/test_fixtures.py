import operator

import pytest

from slash._compat import itervalues, reduce


def test_fixtures(suite, suite_test, defined_fixture):
    suite_test.depend_on_fixture(defined_fixture)
    suite.run()


def test_fixture_cleanup_at_end_of_suite(suite):
    fixture = suite.slashconf.add_fixture()
    suite[-1].depend_on_fixture(fixture)
    cleanup = fixture.add_cleanup()

    summary = suite.run()
    assert cleanup in summary.events


def test_fixture_cleanup_failure_fails_test(suite, suite_test, defined_fixture):
    suite_test.depend_on_fixture(defined_fixture)
    cleanup = defined_fixture.add_cleanup(extra_code=['raise Exception()'])
    suite_test.expect_error()
    suite.run()


def test_fixture_parameters(suite, suite_test, defined_fixture):
    defined_fixture.add_parameter()
    suite_test.depend_on_fixture(defined_fixture)
    summary = suite.run()
    all_results = summary.get_all_results_for_test(suite_test)
    num_combinations = reduce(operator.mul, (len(p.values) for p in defined_fixture.get_parameters()))
    assert len(all_results) == num_combinations


def test_fixture_dependency_chain(suite, suite_test):
    fixture1 = suite.slashconf.add_fixture()
    fixture1.add_parameter()
    fixture2 = suite.slashconf.add_fixture()
    fixture2.add_parameter()
    fixture2.depend_on_fixture(fixture1)
    suite_test.depend_on_fixture(fixture2)
    suite.run()


def test_fixture_dependency_both_directly_and_indirectly(suite, suite_test):

    fixture1 = suite.slashconf.add_fixture()
    num_values1 = 2
    fixture1.add_parameter(num_values=num_values1)

    fixture2 = suite.slashconf.add_fixture()
    num_values2 = 3
    fixture2.add_parameter(num_values=num_values2)
    fixture2.depend_on_fixture(fixture1)

    suite_test.depend_on_fixture(fixture1)
    suite_test.depend_on_fixture(fixture2)

    summary = suite.run()
    results = summary.get_all_results_for_test(suite_test)
    assert len(results) == num_values1 * num_values2


def test_fixture_context(suite, suite_test):
    fixture1 = suite.slashconf.add_fixture()
    fixture1.append_line('assert this == slash.context.fixture')
    fixture2 = suite.slashconf.add_fixture()
    fixture2.append_line('assert this == slash.context.fixture')
    fixture2.depend_on_fixture(fixture1)
    suite_test.depend_on_fixture(fixture1)
    suite.run()
