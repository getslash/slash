# pylint: disable=unused-argument,unused-variable,redefined-outer-name
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


@pytest.mark.parametrize('hook_name', ['session_start', 'test_start'])
def test_sigterm_on_hook(suite, hook_name):
    @gossip.register('slash.{0}'.format(hook_name))
    def session_start():  # pylint: disable=unused-variable
        raise slash.exceptions.TerminatedException('Terminated by signal')

    assert len(suite)
    for index, test in enumerate(suite):
        if index == 0 and hook_name == 'test_start':
            # first test should be interrupted...
            test.expect_interruption()
        else:
            test.expect_deselect()

    result = suite.run(expect_interruption=True)


def test_test_end_called_for_interrupted_test(interrupted_suite, interrupted_test):
    ended = []

    @gossip.register('slash.test_end')
    def test_end():
        ended.append(slash.context.test.__slash__.id)

    s = interrupted_suite.run(expect_interruption=True)
    result = s[interrupted_test]

    assert result.test_metadata.id in ended


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
