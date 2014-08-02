# pylint: disable-msg=W0201
import gossip
import pytest

import slash


def test_interruption(interrupted_suite, interrupted_index):
    interrupted_suite.run(expect_interruption=True)


def test_interruption_triggers_gossip(request, interrupted_suite, interrupted_test):
    test_id = {'value': None}

    @gossip.register('slash.test_interrupt')
    def skip():
        test_id['value'] = slash.test.__slash__.id

    @request.addfinalizer
    def cleanup():
        skip.gossip.unregister()

    results = interrupted_suite.run(expect_interruption=True)
    assert test_id['value'] is not None
    assert results[interrupted_test].test_metadata.id == test_id['value']


def test_critical_cleanups_called(interrupted_suite, interrupted_test):
    interrupted_test.add_cleanup()
    interrupted_suite.run(expect_interruption=True)


def test_non_critical_cleanups_not_called(interrupted_suite, interrupted_test):
    interrupted_test.add_cleanup(critical=True)
    interrupted_suite.run(expect_interruption=True)


@pytest.fixture
def interrupted_suite(populated_suite, interrupted_index):
    for index, test in enumerate(populated_suite):
        if index == interrupted_index:
            test.inject_line('raise KeyboardInterrupt()')
            test.expect_interruption()
        elif index > interrupted_index:
            test.expect_deselect()

    return populated_suite


@pytest.fixture
def interrupted_test(interrupted_suite, interrupted_index):
    return interrupted_suite[interrupted_index]


@pytest.fixture
def interrupted_index(populated_suite):
    return int(len(populated_suite) // 2)
