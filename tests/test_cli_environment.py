from .utils import TestCase
from confetti import Config
from slash import plugins
from slash._compat import cStringIO
from slash.utils import conf_utils
from slash.utils import cli_utils
from slash.plugins import PluginInterface
import sys

class OutputCaptureTest(TestCase):
    def setUp(self):
        super(OutputCaptureTest, self).setUp()
        self.stderr = cStringIO()
        self.forge.replace_with(sys, "stderr", self.stderr)
        self.stdout = cStringIO()
        self.forge.replace_with(sys, "stdout", self.stdout)

class ArgumentParsingTest(OutputCaptureTest):
    def setUp(self):
        super(ArgumentParsingTest, self).setUp()
        self.config = Config({
            "a": {"a1": {"flag1": True // conf_utils.Cmdline(off="--no-flag1")}},
            "b": {"b1": {"flag2": False // conf_utils.Cmdline(on="--flag2")}},
            "string_value" : "",
            "int_value" : 0,
            })

    def test_config_off_flag(self):
        with cli_utils.get_cli_environment_context(argv=["--no-flag1"], config=self.config):
            self.assertFalse(self.config["a"]["a1"]["flag1"])
        self.assertTrue(self.config["a"]["a1"]["flag1"])

    def test_config_on_flag(self):
        with cli_utils.get_cli_environment_context(argv=["--flag2"], config=self.config):
            self.assertTrue(self.config["b"]["b1"]["flag2"])
        self.assertFalse(self.config["b"]["b1"]["flag2"])

    def test_config_assign_flag(self):
        with cli_utils.get_cli_environment_context(argv=["-o", "string_value=hello", "-o", "int_value=666"], config=self.config):
            self.assertEquals(self.config.root.string_value, "hello")
            self.assertEquals(self.config.root.int_value, 666)

    def test_config_assign_wrong_path_restores_config(self):
        "Given a bad override, the get_parsed_config_args_context() should leave the configuration untouched"
        with self.assertRaises(SystemExit) as caught:
            with cli_utils.get_cli_environment_context(argv=["-o", "string_value=bla", "-o", "int_value=hello"],
                                                       config=self.config):
                pass
        self.assertNotEquals(caught.exception.code, 0)
        self.assertEquals(self.config.root.int_value, 0)
        self.assertEquals(self.config.root.string_value, "")

class PluginCommandLineArgumentsTest(OutputCaptureTest):
    def setUp(self):
        super(PluginCommandLineArgumentsTest, self).setUp()
        self.plugin = SampleCommandLinePlugin()
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
    def test_arguments_are_not_parsed_if_not_activated(self):
        args = ["--start-session-option", "2"]
        with self.assertRaises(SystemExit):
            with cli_utils.get_cli_environment_context(argv=args):
                pass
    def test_activation(self):
        with cli_utils.get_cli_environment_context(argv=["--with-sample-plugin"]):
            self.assertIn(self.plugin.get_name(), plugins.manager.get_active_plugins(), "plugin was not activated")

    def test_deactivation(self):
        plugins.manager.activate(self.plugin)
        with cli_utils.get_cli_environment_context(argv=["--without-sample-plugin"]):
            self.assertNotIn(self.plugin.get_name(), plugins.manager.get_active_plugins())
        self.assertIn(self.plugin.get_name(), plugins.manager.get_active_plugins())

    def test_argument_passing(self):
        with cli_utils.get_cli_environment_context(argv=["--with-sample-plugin", "--plugin-option", "value"]):
            self.assertEquals(self.plugin.cmdline_param, "value")

    def test_help_shows_available_plugins(self):
        with self.assertRaises(SystemExit):
            with cli_utils.get_cli_environment_context(argv=["-h"]):
                pass
        output = self.stdout.getvalue()
        self.assertIn("--with-sample-plugin", output)

class SampleCommandLinePlugin(PluginInterface):
    def get_name(self):
        return "sample-plugin"
    def configure_argument_parser(self, parser):
        parser.add_argument("--plugin-option")
    def configure_from_parsed_args(self, args):
        self.cmdline_param = args.plugin_option
