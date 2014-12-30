import slash
from slash import plugins
from slash.plugins import PluginInterface
from slash import hooks
import pytest
import gossip

from .utils import TestCase


class SessionEndException(Exception):
    pass


class SessionStartException(Exception):
    pass


class TestEndException(Exception):
    pass


def test_hook__test_interrupt(populated_suite, request, checkpoint):
    request.addfinalizer(
        hooks.test_interrupt.register(checkpoint)
        .unregister)

    test_index = int(len(populated_suite) / 2)
    for index, test in enumerate(populated_suite):
        if index == test_index:
            test.interrupt()
        elif index > test_index:
            test.expect_deselect()
    populated_suite.run(expect_interruption=True)
    assert checkpoint.called

def test_hook__test_failure_without_exception(populated_suite, request, checkpoint, suite_test):
    request.addfinalizer(
        hooks.test_failure.register(checkpoint)
        .unregister)

    suite_test.inject_line('slash.add_failure("failure")')
    suite_test.expect_failure()

    populated_suite.run()
    assert checkpoint.called


@pytest.mark.parametrize(
    'hook_exception', [
        ('slash.session_start', SessionStartException),
        ('slash.session_end', SessionEndException),
        ('slash.test_end', TestEndException)])
@pytest.mark.parametrize('debug_enabled', [True, False])
def test_debugger_called_on_hooks(hook_exception, request, forge, config_override, checkpoint, debug_enabled):
    hook_name, exception_type = hook_exception

    @gossip.register(hook_name)
    def raise_exc():
        raise exception_type()

    request.addfinalizer(raise_exc.gossip.unregister)
    config_override("debug.enabled", debug_enabled)

    def test_something():
        pass

    forge.replace_with(slash.utils.debug, 'launch_debugger', checkpoint)

    with pytest.raises(exception_type):
        with slash.Session() as s:
            with s.get_started_context():
                slash.runner.run_tests(slash.loader.Loader().get_runnables(test_something))

    assert checkpoint.called == debug_enabled
    if debug_enabled:
        assert checkpoint.args[0][0] is exception_type
        assert type(checkpoint.args[0][1]) is exception_type


#### Older tests below, need modernizing ####

class HookCallingTest(TestCase):

    def setUp(self):
        super(HookCallingTest, self).setUp()
        self.plugin1 = make_custom_plugin("plugin1", self)
        self.plugin2 = make_custom_plugin("plugin2", self, hook_names=["session_start", "after_session_start"])
        self.addCleanup(plugins.manager.uninstall, self.plugin1)
        self.addCleanup(plugins.manager.uninstall, self.plugin2)

    def test_hook_calling_order(self):
        # expect:
        with self.forge.any_order():
            self.plugin1.activate()
            self.plugin2.activate()

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
