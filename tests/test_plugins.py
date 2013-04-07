from .utils import TestCase
from shakedown import hooks
from shakedown import plugins
from shakedown.plugins import PluginInterface
from shakedown.plugins import IncompatiblePlugin
from tempfile import mkdtemp
import os

class PluginInstallationTest(TestCase):
    def test_cannot_install_incompatible_subclasses(self):
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
        self.root_path = mkdtemp()
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
import shakedown.plugins
from shakedown.plugins.interface import PluginInterface

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
                    f.write("     shakedown.plugins.manager.install({name}())".format(name=plugin_name))
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
        super(PluginDiscoveryTest, self).tearDown()
    def test_discovery(self):
        plugins.manager.discover()
        self.assertEquals(
            set(plugins.manager.get_installed_plugins().keys()),
            self.expected_names
        )


class PluginActivationTest(TestCase):
    def setUp(self):
        super(PluginActivationTest, self).setUp()
        self.plugin = StartSuitePlugin()

    def test_get_active_plugins(self):
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        self.assertEquals(plugins.manager.get_active_plugins(), {})
        plugins.manager.activate(self.plugin)
        self.assertEquals(
            plugins.manager.get_active_plugins(),
            {self.plugin.get_name() : self.plugin}
        )
        plugins.manager.deactivate(self.plugin)
        self.assertEquals(plugins.manager.get_active_plugins(), {})

    def test_hook_registration(self):
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        hooks.suite_start()
        self.assertEquals(self.plugin.suite_start_call_count, 0)
        plugins.manager.activate(self.plugin)
        hooks.suite_start()
        self.assertEquals(self.plugin.suite_start_call_count, 1)
        plugins.manager.deactivate(self.plugin)
        hooks.suite_start()
        self.assertEquals(self.plugin.suite_start_call_count, 1)

    def test_uninstall_also_deactivates(self):
        plugins.manager.install(self.plugin)
        plugins.manager.activate(self.plugin)
        plugins.manager.uninstall(self.plugin)
        hooks.suite_start()
        self.assertEquals(self.plugin.suite_start_call_count, 0)

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


class StartSuitePlugin(PluginInterface):
    def __init__(self):
        super(StartSuitePlugin, self).__init__()
        self.suite_start_call_count = 0
    def get_name(self):
        return "start-suite"
    def suite_start(self):
        self.suite_start_call_count += 1
