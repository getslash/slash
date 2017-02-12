# pylint: disable=unused-argument, unused-variable
from slash._compat import ExitStack
import slash
from slash import plugins
from slash.plugins import PluginInterface
from slash import hooks
import pytest
import gossip

from .utils import TestCase, make_runnable_tests, CustomException


class SessionEndException(Exception):
    pass


class SessionStartException(Exception):
    pass


class TestEndException(Exception):
    pass


class BeforeTestCleanupException(Exception):
    pass


def test_test_skip_hook(suite, suite_test, checkpoint):
    slash.hooks.test_skip.register(checkpoint)  # pylint: disable=no-member

    suite_test.when_run.skip()

    suite.run()
    assert checkpoint.called_count == 1


@pytest.mark.parametrize('autouse', [True, False])
def test_test_start_before_fixture_start(suite, suite_test, defined_fixture, autouse):
    if autouse:
        assert not defined_fixture.autouse # make sure we're not obsolete code and that that's still where it is
        defined_fixture.autouse = True
    else:
        suite_test.depend_on_fixture(defined_fixture)
    event_code = suite.slashconf.add_hook_event('test_start', extra_args=['slash.context.test.__slash__.id'])

    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    test_id = result.test_metadata.id

    event = summary.events[event_code, test_id]

    assert summary.events['fixture_start', defined_fixture.id].timestamp > event.timestamp


def test_last_test_end_after_session_cleanup(suite, last_suite_test):
    test = last_suite_test
    @test.append_body
    def __code__(): # pylint: disable=unused-variable
        import gossip # pylint: disable=redefined-outer-name,reimported
        # pylint: disable=undefined-variable,unused-variable
        def session_cleanup_callback():
            __ut__.events.add('session_cleanup')
        slash.add_cleanup(session_cleanup_callback, scope='session')

        @gossip.register('slash.test_end')
        def test_end_callback():
            __ut__.events.add('test_end')

    events = suite.run().events

    assert events['test_end'].timestamp < events['session_cleanup'].timestamp


def test_no_error_hooks_called_on_success(suite):

    called = []

    for hook_name in ['test_error', 'test_failure', 'test_skip', 'error_added']:
        gossip.register(lambda name=hook_name, **kw: called.append(name), 'slash.{0}'.format(hook_name))

    suite.run()
    assert not called


def test_hook__error_added_during_test(suite, request, checkpoint, suite_test):

    request.addfinalizer(
        hooks.error_added.register(checkpoint)  # pylint: disable=no-member
        .unregister)

    suite_test.when_run.raise_exception()

    summary = suite.run()
    assert checkpoint.called
    [result] = summary.get_all_results_for_test(suite_test)
    assert checkpoint.kwargs['result'] is result


def test_hook__error_added_after_test(suite, request, checkpoint, suite_test):

    request.addfinalizer(
        hooks.error_added.register(checkpoint)  # pylint: disable=no-member
        .unregister)

    summary = suite.run()
    assert not checkpoint.called
    [result] = summary.get_all_results_for_test(suite_test)
    try:
        1 / 0
    except:
        result.add_error()
    assert checkpoint.called
    assert checkpoint.kwargs['result'] is result
    assert 'ZeroDivisionError' in str(checkpoint.kwargs['error'])


def test_hook__test_interrupt(suite, request, checkpoint):
    request.addfinalizer(
        hooks.test_interrupt.register(checkpoint)  # pylint: disable=no-member
        .unregister)

    test_index = int(len(suite) / 2)
    for index, test in enumerate(suite):
        if index == test_index:
            test.when_run.interrupt()
        elif index > test_index:
            test.expect_deselect()
    suite.run(expect_interruption=True)
    assert checkpoint.called


def test_hook__test_failure_without_exception(suite, request, checkpoint, suite_test):
    request.addfinalizer(
        hooks.test_failure.register(checkpoint)  # pylint: disable=no-member
        .unregister)

    suite_test.append_line('slash.add_failure("failure")')
    suite_test.expect_failure()

    suite.run()
    assert checkpoint.called


@pytest.mark.parametrize(
    'hook_exception', [
        ('slash.session_start', SessionStartException, True),
        ('slash.session_end', SessionEndException, True),
        ('slash.test_end', TestEndException, True),
        ('slash.before_test_cleanups', BeforeTestCleanupException, False)])
@pytest.mark.parametrize('debug_enabled', [True, False])
def test_debugger_called_on_hooks(hook_exception, request, forge, config_override, checkpoint, debug_enabled):
    hook_name, exception_type, should_raise = hook_exception

    @gossip.register(hook_name)
    def raise_exc():
        raise exception_type()

    config_override("debug.enabled", debug_enabled)

    def test_something():
        pass

    forge.replace_with(slash.utils.debug, 'launch_debugger', checkpoint)

    with ExitStack() as exception_stack:
        if should_raise:
            exception_stack.enter_context(pytest.raises(exception_type))
        with slash.Session() as s:
            with s.get_started_context():
                slash.runner.run_tests(make_runnable_tests(test_something))

    assert checkpoint.called == debug_enabled
    if debug_enabled:
        assert checkpoint.args[0][0] is exception_type
        assert type(checkpoint.args[0][1]) is exception_type  # pylint: disable=unidiomatic-typecheck


def test_before_cleanup_hook(request, forge):
    cleanup = forge.create_wildcard_function_stub(name='cleanup')
    before_cleanup_hook = forge.create_wildcard_function_stub(name='before_test_cleanup')
    test_end_hook = forge.create_wildcard_function_stub(name='test_end')
    gossip.register(before_cleanup_hook, 'slash.before_test_cleanups')
    gossip.register(test_end_hook, 'slash.test_end')

    before_cleanup_hook()
    cleanup()
    test_end_hook()

    forge.replay()

    def test_something():
        slash.add_cleanup(cleanup)

    with slash.Session() as s:
        with s.get_started_context():
            slash.runner.run_tests(make_runnable_tests(test_something))


def test_session_end_not_called_when_before_session_start_fails(checkpoint):

    @gossip.register('slash.before_session_start')
    def before_start_hook():
        raise CustomException()

    @gossip.register('slash.session_end')
    def hook():
        checkpoint()


    with slash.Session() as s:
        with pytest.raises(CustomException):
            with s.get_started_context():
                pass

    [err] = s.results.global_result.get_errors()
    assert 'CustomException' in str(err)
    assert not checkpoint.called


#### Older tests below, need modernizing ####

class HookCallingTest(TestCase):

    def setUp(self):
        super(HookCallingTest, self).setUp()
        self.plugin1 = make_custom_plugin("plugin1", self)
        self.plugin2 = make_custom_plugin("plugin2", self, hook_names=["before_session_start", "session_start", "after_session_start"])
        self.addCleanup(plugins.manager.uninstall, self.plugin1)
        self.addCleanup(plugins.manager.uninstall, self.plugin2)

    def test_hook_calling_order(self):
        # pylint: disable=no-member
        # expect:
        with self.forge.any_order():
            self.plugin1.activate()
            self.plugin2.activate()

        with self.forge.any_order():
            self.plugin1.before_session_start()
            self.plugin2.before_session_start()

        with self.forge.any_order():
            self.plugin1.session_start()
            self.plugin2.session_start()

        with self.forge.any_order():
            self.plugin1.after_session_start()
            self.plugin2.after_session_start()

        self.plugin1.session_end()

        self.forge.replay()
        # get:

        plugins.manager.install(self.plugin1, activate=True)
        plugins.manager.install(self.plugin2, activate=True)

        with slash.Session() as s:
            with s.get_started_context():
                pass


def make_custom_plugin(name, test, hook_names=None):

    class CustomPlugin(PluginInterface):

        def get_name(self):
            return name

    CustomPlugin.__name__ = name

    if hook_names is None:
        hook_names = [name for name, _ in slash.hooks.get_all_hooks()]

    for hook_name in hook_names:
        setattr(CustomPlugin, hook_name, test.forge.create_wildcard_function_stub(name=hook_name))

    setattr(CustomPlugin, "activate", test.forge.create_wildcard_function_stub(name="activate"))

    return CustomPlugin()
