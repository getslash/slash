# pylint: disable=unused-argument,unused-variable,redefined-outer-name
import gossip
import pytest

import slash
import slash.hooks

from .conftest import Checkpoint


def test_interruption(interrupted_suite, interrupted_index):
    interrupted_suite.run(expect_interruption=True)


def test_interruption_added_to_result(interrupted_suite, interrupted_index):
    caught = []
    @gossip.register('slash.interruption_added')
    def interruption_added(result, exception):
        caught.append(exception)

    summary = interrupted_suite.run(expect_interruption=True)
    assert len(caught) == 1
    [err] = caught              # pylint: disable=unbalanced-tuple-unpacking
    assert err.exception_type is KeyboardInterrupt


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

    assert suite
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


def test_session_interruption_in_start(suite, suite_test, session_interrupt):

    @suite.slashconf.append_body
    def __code__():
        @slash.hooks.session_start.register # pylint: disable=no-member
        def session_cleanup():
            raise KeyboardInterrupt()

    for test in suite:
        test.expect_deselect()

    suite.run(expect_interruption=True)

    assert session_interrupt.called_count == 1


def test_interrupt_hooks_should_be_called_once(suite, suite_test, is_last_test, session_interrupt, test_interrupt_callback):

    @suite_test.append_body
    def __code__():
        @slash.add_critical_cleanup
        def cleanup():
            raise KeyboardInterrupt('A')
        raise KeyboardInterrupt('B')

    suite_test.expect_interruption()

    for t in suite.iter_all_after(suite_test, assert_has_more=not is_last_test):
        t.expect_deselect()

    result = suite.run(expect_interruption=True)

    assert test_interrupt_callback.called_count == 1
    assert session_interrupt.called_count == 1
    assert result.session.results.global_result.is_interrupted()


def test_interrupted_with_custom_exception(suite, suite_test, request):

    import test

    class CustomException(Exception):
        pass
    test.__interruption_exception__ = CustomException

    prev_interruption_exceptions = slash.exceptions.INTERRUPTION_EXCEPTIONS
    slash.exceptions.INTERRUPTION_EXCEPTIONS += (CustomException,)

    @request.addfinalizer
    def cleanup():
        del test.__interruption_exception__
        slash.exceptions.INTERRUPTION_EXCEPTIONS = prev_interruption_exceptions


    suite_test.append_line('import test')
    suite_test.append_line('raise test.__interruption_exception__()')
    suite_test.expect_interruption()

    for t in suite.iter_all_after(suite_test):
        t.expect_deselect()

    results = suite.run(expect_interruption=True)


def test_test_interrupt_hook_exception(suite_builder):
    # pylint: disable=reimported,redefined-outer-name
    @suite_builder.first_file.add_code
    def __code__():
        import slash

        @slash.hooks.test_interrupt.register # pylint: disable=no-member
        def test_interrupt(**_):
            1/0 # pylint: disable=pointless-statement


        def test_1():
            raise KeyboardInterrupt()

        def test_2():
            pass

    [res] = suite_builder.build().run().assert_results(1)
    assert res.is_interrupted()



@pytest.fixture
def session_interrupt():
    callback = Checkpoint()
    slash.hooks.session_interrupt.register(callback) # pylint: disable=no-member
    return callback


@pytest.fixture
def test_interrupt_callback():
    callback = Checkpoint()
    slash.hooks.test_interrupt.register(callback) # pylint: disable=no-member
    return callback


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
