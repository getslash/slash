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

    summary = interrupted_suite.run(expect_interruption=True)
    assert test_id['value'] is not None
    for result in summary.get_all_results_for_test(interrupted_test):
        assert result.test_metadata.id == test_id['value']


def test_critical_cleanups_called(interrupted_suite, interrupted_test):
    cleanup = interrupted_test.add_deferred_event(
        'slash.add_critical_cleanup', 'critical_cleanup')
    summary = interrupted_suite.run(expect_interruption=True)
    assert cleanup in summary.events


def test_non_critical_cleanups_not_called(interrupted_suite, interrupted_test):
    cleanup = interrupted_test.add_cleanup()
    summary = interrupted_suite.run(expect_interruption=True)
    assert cleanup not in summary.events


def test_sigterm_interrupt(suite, suite_test):
    suite_test.append_line('raise slash.exceptions.TerminatedException()')
    suite_test.expect_interruption()
    for test in suite.iter_all_after(suite_test):
        test.expect_deselect()
    suite.run(expect_interruption=True)


@pytest.fixture
def interrupted_suite(suite, interrupted_index):
    for index, test in enumerate(suite):
        if index == interrupted_index:
            test.append_line('raise KeyboardInterrupt()')
            test.expect_interruption()
        elif index > interrupted_index:
            test.expect_deselect()

    return suite


@pytest.fixture
def interrupted_test(interrupted_suite, interrupted_index):
    return interrupted_suite[interrupted_index]


@pytest.fixture
def interrupted_index(suite):
    return int(len(suite) // 2)
