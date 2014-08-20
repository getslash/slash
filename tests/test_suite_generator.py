"""
Tests for the suite generation utility (used to commit suite directories and assert expected results)
"""
import itertools

import pytest

from slash._compat import iteritems, itervalues


def test_iter_fixture_variations_no_variation(planned_test):
    assert list(planned_test.iter_expected_fixture_variations()) == [None]

def test_iter_params_no_params(planned_test):
    assert list(planned_test.iter_parametrization_variations()) == [None]

def test_iter_params(planned_test):
    planned_test.parametrize(num_params=2)
    assert len(list(planned_test.iter_parametrization_variations())) == 2
    planned_test.parametrize(num_params=3)
    assert len(list(planned_test.iter_parametrization_variations())) == 6


def test_iter_fixture_variations_shallow(suite, planned_test):
    """ Test iteration with no fixture parametrization"""
    fixtures = [planned_test.add_fixture(suite.add_fixture())
                for i in range(3)]

    variations = list(planned_test.iter_expected_fixture_variations())

    assert len(variations) == 1

    assert variations == [dict((f.name, {'value': f.value, 'params': {}}) for f in fixtures)]


def test_iter_fixture_variations_parametrized(suite, planned_test):
    """ Test iteration with no fixture parametrization"""
    fixtures = [planned_test.add_fixture(suite.add_fixture())
                for i in range(2)]

    for fixture in fixtures:
        for i in range(2):
            fixture.parametrize()

    # for each fixture, the possible param dicts it can yield (as lists)
    param_dicts_ordered_by_fixture = []
    for fixture in fixtures:
        fixture_param_dicts = []
        param_names = []
        param_value_options = []
        for param_name, options in iteritems(fixture.params):
            param_names.append(param_name)
            param_value_options.append(options)

        for combination in itertools.product(*itervalues(fixture.params)):
            fixture_param_dicts.append(dict(zip(fixture.params, combination)))

        param_dicts_ordered_by_fixture.append(fixture_param_dicts)


    expected = [dict((f.name, {'value': f.value, 'params': param_dict})
                     for f, param_dict in zip(fixtures, dict_combination))
                for dict_combination in itertools.product(*param_dicts_ordered_by_fixture)]

    got = list(planned_test.iter_expected_fixture_variations())

    assert len(expected) == len(got)

    # we can't use sets here, and sorting the two lists is a nightmare in Python 3 since they contain dicts
    for expected_dict in expected:
        got.remove(expected_dict)
    assert not got


@pytest.mark.parametrize('regular_function', [True, False])
def test_iter_fixture_variations_dependent_fixtures(suite, regular_function):
    test = suite.add_test(regular_function=regular_function)

    fixture1 = suite.add_fixture()
    fixture1.parametrize(num_params=3)
    fixture2 = suite.add_fixture()
    fixture2.parametrize(num_params=2)
    fixture2.add_fixture(fixture1)

    test.add_fixture(fixture1)
    test.add_fixture(fixture2)

    variations = list(test.iter_expected_fixture_variations())
    assert len(variations) == 6
    for variation in variations:
        assert variation[fixture1.name]['params'] == variation[fixture2.name]['params'][fixture1.name]['params']


@pytest.fixture
def planned_test(suite):
    return suite.add_test()
