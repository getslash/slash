import os

import gossip
import pytest
import slash
from slash._compat import PY2
from slash import hooks, plugins
from slash.plugins import IncompatiblePlugin, PluginInterface

from .utils import CustomException, TestCase


@pytest.fixture
def restore_plugins_on_cleanup(request):
    request.addfinalizer(plugins.manager.install_builtin_plugins)
    request.addfinalizer(plugins.manager.uninstall_all)


@pytest.fixture(autouse=True, scope="function")
def reset_gossip(request):
    @request.addfinalizer
    def cleanup():
        for group in list(gossip.get_groups()):
            if group.name == 'slash':
                continue
            group.undefine()

        for hook in gossip.get_all_hooks():
            if hook.group.name != 'slash':
                hook.undefine()
            else:
                hook.unregister_all()


def test_registers_on_none(restore_plugins_on_cleanup, checkpoint):

    @slash.plugins.active
    class SamplePlugin(PluginInterface):

        def get_name(self):
            return 'sample'

        @plugins.registers_on(None)
        def some_method_here(self):
            checkpoint()

    gossip.trigger('slash.some_method_here')
    assert not checkpoint.called



def test_registers_on_with_private_methods(restore_plugins_on_cleanup, checkpoint):

    @slash.plugins.active
    class SamplePlugin(PluginInterface):

        def get_name(self):
            return 'sample'

        @plugins.registers_on('some_hook')
        def _handler(self):
            checkpoint()

    assert not checkpoint.called
    gossip.trigger('some_hook')
    assert checkpoint.called


def test_class_variables_allowed(restore_plugins_on_cleanup):
    @slash.plugins.active
    class SamplePlugin(PluginInterface):

        ATTRIBUTE = 'some_value'

        def get_name(self):
            return 'sample'


def test_active_decorator(restore_plugins_on_cleanup):

    plugins.manager.uninstall_all()

    @slash.plugins.active
    class SamplePlugin(PluginInterface):

        def get_name(self):
            return 'sample'

    assert isinstance(SamplePlugin, type)
    assert issubclass(SamplePlugin, PluginInterface)
    [active] = plugins.manager.get_active_plugins().values()
    assert isinstance(active, SamplePlugin)


def test_custom_hook_registration():

    hook_name = 'some_hook'
    with pytest.raises(LookupError):
        gossip.get_hook(hook_name)

    class MyPlugin(PluginInterface):

        def get_name(self):
            return "plugin"

        @plugins.registers_on(hook_name)
        def unknown(self):
            pass
    p = MyPlugin()
    plugins.manager.install(p, activate=True)
    registrations = gossip.get_hook(hook_name).get_registrations()
    assert 1 == len(registrations)
    [r] = registrations
    if PY2:
        assert r.func.__func__ is MyPlugin.unknown.__func__
    else:
        assert r.func.__func__ is MyPlugin.unknown

    # make sure we deactivate properly as well
    plugins.manager.deactivate(p)
    assert not gossip.get_hook(hook_name).get_registrations()


def test_register_invalid_hook():

    initially_installed = list(plugins.manager.get_installed_plugins())

    class MyPlugin(PluginInterface):

        def get_name(self):
            return "plugin"

        def unknown(self):
            pass

    with pytest.raises(IncompatiblePlugin):
        plugins.manager.install(MyPlugin(), activate=True)

    assert list(plugins.manager.get_installed_plugins()) == initially_installed


def test_register_custom_hooks_strict_group():

    initially_installed = list(plugins.manager.get_installed_plugins())

    hook_name = "some_group.some_hook"
    gossip.get_or_create_group("some_group").set_strict()

    class MyPlugin(PluginInterface):

        def get_name(self):
            return "plugin"

        @plugins.registers_on(hook_name)
        def unknown(self):
            pass

    with pytest.raises(IncompatiblePlugin):
        plugins.manager.install(MyPlugin(), activate=True)

    assert list(plugins.manager.get_installed_plugins()) == initially_installed


def test_builtin_plugins_hooks_start_condition():
    "make sure that all hooks are either empty, or contain callbacks marked with `slash.<identifier>`"
    for hook_name, hook in hooks.get_all_hooks():
        for registration in hook.get_registrations():
            assert registration.token.startswith('slash.'), 'Callback {0}.{1} is not a builtin!'.format(hook_name, identifier)

def test_builtin_plugins_are_installed():
    installed = plugins.manager.get_installed_plugins()
    assert installed
    for filename in os.listdir(os.path.join(os.path.dirname(plugins.__file__), "builtin")):
        if filename.startswith("_") or filename.startswith(".") or not filename.endswith(".py"):
            continue
        assert filename[:(-3)] in installed


class PluginInstallationTest(TestCase):

    def test_cannot_install_incompatible_subclasses(self):
        plugins.manager.uninstall_all()
        self.addCleanup(plugins.manager.install_builtin_plugins)

        class Incompatible(object):
            pass
        for invalid in (Incompatible, Incompatible(), PluginInterface, object(), 1, "string"):
            with self.assertRaises(IncompatiblePlugin):
                plugins.manager.install(invalid)
        self.assertEquals(plugins.manager.get_installed_plugins(), {})

    def test_install_uninstall(self):
        plugin_name = "some_plugin_name"

        class CustomPlugin(PluginInterface):

            def get_name(self):
                return plugin_name
        with self.assertRaises(LookupError):
            plugins.manager.get_plugin(plugin_name)
        plugin = CustomPlugin()
        plugins.manager.install(plugin)
        self.assertIs(plugins.manager.get_plugin(plugin_name), plugin)
        plugins.manager.uninstall(plugin)
        with self.assertRaises(LookupError):
            plugins.manager.get_plugin(plugin_name)


class PluginDiscoveryTest(TestCase):

    def setUp(self):
        super(PluginDiscoveryTest, self).setUp()
        self.root_path = self.get_new_path()
        self.expected_names = set()
        for index, path in enumerate([
                "a/b/p1.py",
                "a/b/p2.py",
                "a/p3.py",
                "a/b/c/p4.py",
        ]):
            plugin_name = "auto_plugin_{0}".format(index)
            path = os.path.join(self.root_path, path)
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            with open(path, "w") as f:
                f.write("""
import slash.plugins
from slash.plugins.interface import PluginInterface

class {name}(PluginInterface):
    def get_name(self):
        return {name!r}

def install_plugins():
""".format(name=plugin_name))
                if index % 2 == 0:
                    # don't install
                    f.write("     pass")
                else:
                    self.expected_names.add(plugin_name)
                    f.write("     slash.plugins.manager.install({name}())".format(name=plugin_name))
        for junk_file in [
                "a/junk1.p",
                "a/b/junk2",
                "a/b/c/junk3",
        ]:
            with open(os.path.join(self.root_path, junk_file), "w") as f:
                f.write("---JUNK----")
        self.override_config("plugins.search_paths", [self.root_path])

    def tearDown(self):
        plugins.manager.uninstall_all()
        plugins.manager.install_builtin_plugins()
        super(PluginDiscoveryTest, self).tearDown()

    def test_discovery(self):
        plugins.manager.uninstall_all()
        self.addCleanup(plugins.manager.install_builtin_plugins)
        plugins.manager.discover()
        self.assertEquals(
            set(plugins.manager.get_installed_plugins().keys()),
            self.expected_names
        )


class PluginActivationTest(TestCase):

    def setUp(self):
        super(PluginActivationTest, self).setUp()
        self.plugin = StartSessionPlugin()

    def test_get_active_plugins(self):
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        self.assertEquals(plugins.manager.get_active_plugins(), {})
        plugins.manager.activate(self.plugin)
        self.assertEquals(
            plugins.manager.get_active_plugins(),
            {self.plugin.get_name(): self.plugin}
        )
        plugins.manager.deactivate(self.plugin)
        self.assertEquals(plugins.manager.get_active_plugins(), {})

    def test_deactivaion_no_activation(self):
        plugins.manager.install(self.plugin)
        self.assertFalse(self.plugin._deactivate_called)
        plugins.manager.uninstall(self.plugin)
        self.assertFalse(self.plugin._deactivate_called, "Deactivate called even though plugin not activated")

    def test_activation_exception(self):
        self.plugin.activate = CustomException.do_raise
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)

        with self.assertRaises(CustomException):
            plugins.manager.activate(self.plugin)

        # make sure no registrations are in effect...
        self.assert_hooks_not_registered()

        plugins.manager.deactivate(self.plugin)
        self.assertFalse(self.plugin._deactivate_called, "Deactivate unexpectedly called!")

    def test_deactivation_exception(self):
        self.plugin.deactivate = CustomException.do_raise
        plugins.manager.install(self.plugin, activate=True)
        self.addCleanup(plugins.manager.uninstall, self.plugin)

        with self.assertRaises(CustomException):
            plugins.manager.deactivate(self.plugin)
        self.assert_hooks_not_registered()

    def test_activate_called(self):
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        self.assertFalse(self.plugin._activate_called)
        plugins.manager.activate(self.plugin)
        self.assertTrue(self.plugin._activate_called)

    def test_deactivate_called_on_deactivate(self):
        plugins.manager.install(self.plugin)
        self.assertFalse(self.plugin._deactivate_called)
        plugins.manager.activate(self.plugin)
        self.assertFalse(self.plugin._deactivate_called)
        plugins.manager.deactivate(self.plugin)
        self.assertTrue(self.plugin._deactivate_called)

    def test_hook_registration(self):
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        self.assert_hooks_not_registered()
        plugins.manager.activate(self.plugin)
        hooks.session_start()
        self.assertEquals(self.plugin.session_start_call_count, 1)
        plugins.manager.deactivate(self.plugin)
        hooks.session_start()
        self.assertEquals(self.plugin.session_start_call_count, 1)

    def test_install_and_activate(self):
        """test plugins.manager.install(..., activate=True)"""
        plugins.manager.install(self.plugin, activate=True)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        self.assertIn(self.plugin.get_name(), plugins.manager.get_active_plugins())

    def test_uninstall_also_deactivates(self):
        plugins.manager.install(self.plugin)
        plugins.manager.activate(self.plugin)
        plugins.manager.uninstall(self.plugin)
        hooks.session_start()
        self.assertEquals(self.plugin.session_start_call_count, 0)

    def test_cannot_activate_uninstalled_plugin(self):
        class Plugin(PluginInterface):

            def get_name(self):
                return "Test plugin"
        with self.assertRaisesRegexp(ValueError, ".*not installed.*"):
            plugins.manager.activate(Plugin())

    def test_unknown_hook_names(self):
        "Make sure that plugins with unknown hook names get discarded"
        class Plugin(PluginInterface):

            def get_name(self):
                return "Test plugin"

            def unknown_hook_1(self):
                pass

        plugin = Plugin()
        plugins.manager.install(plugin)
        self.addCleanup(plugins.manager.uninstall, plugin)
        with self.assertRaisesRegexp(IncompatiblePlugin, r"\bUnknown hooks\b.*"):
            plugins.manager.activate(plugin)

    def test_custom_hook_names(self):
        "Make sure that plugins with unknown hook names get discarded"
        class Plugin(PluginInterface):

            def get_name(self):
                return "Test plugin"

            def custom_hook(self):
                pass

        hooks.add_custom_hook("custom_hook")
        self.addCleanup(hooks.remove_custom_hook, "custom_hook")
        plugin = Plugin()
        plugins.manager.install(plugin, activate=True)
        self.addCleanup(plugins.manager.uninstall, plugin)

    def assert_hooks_not_registered(self):
        hooks.session_start()
        self.assertEquals(self.plugin.session_start_call_count, 0, "Hook unexpectedly registered!")


class StartSessionPlugin(PluginInterface):
    _activate_called = False
    _deactivate_called = False

    def __init__(self):
        super(StartSessionPlugin, self).__init__()
        self.session_start_call_count = 0

    def get_name(self):
        return "start-session"

    def session_start(self):
        self.session_start_call_count += 1

    def activate(self):
        self._activate_called = True

    def deactivate(self):
        self._deactivate_called = True
