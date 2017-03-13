import sys

from confetti import Config
from slash import plugins
from slash._compat import cStringIO
from slash.plugins import PluginInterface
from slash.utils import cli_utils, conf_utils

from .utils import TestCase


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
            "string_value": "",
            "int_value": 0 // conf_utils.Cmdline(increase="--increase", decrease="--decrease"),
            "arg_value": "" // conf_utils.Cmdline(arg="--arg-value"),
            "list": ["existing_item"] // conf_utils.Cmdline(append="--append"),
        })
        self._parser = cli_utils.SlashArgumentParser()
        cli_utils.configure_arg_parser_by_config(self._parser, self.config)

    def _cli(self, argv):
        parsed_args, _ = self._parser.parse_known_args(argv)
        return cli_utils.get_modified_configuration_from_args_context(self._parser, parsed_args, config=self.config)

    def test_config_arg_flag(self):
        with self._cli(["--arg-value=x"]):
            self.assertEqual(self.config["arg_value"], "x")

    def test_config_increase(self):
        with self._cli(["--increase"]):
            self.assertEqual(self.config["int_value"], 1)

    def test_config_decrease(self):
        with self._cli(["--decrease"]):
            self.assertEqual(self.config["int_value"], -1)

    def test_config_off_flag(self):
        with self._cli(["--no-flag1"]):
            self.assertFalse(self.config["a"]["a1"]["flag1"])
        self.assertTrue(self.config["a"]["a1"]["flag1"])

    def test_config_on_flag(self):
        with self._cli(["--flag2"]):
            self.assertTrue(self.config["b"]["b1"]["flag2"])
        self.assertFalse(self.config["b"]["b1"]["flag2"])

    def test_config_append_flag(self):
        with self._cli(["--append", "a", "--append=b"]):
            self.assertEqual(self.config["list"], ["existing_item", "a", "b"])

    def test_config_assign_flag(self):
        with self._cli(["-o", "string_value=hello", "-o", "int_value=666"]):
            self.assertEqual(self.config.root.string_value, "hello")
            self.assertEqual(self.config.root.int_value, 666)

    def test_config_assign_wrong_path_restores_config(self):
        "Given a bad override, the get_parsed_config_args_context() should leave the configuration untouched"
        with self.assertRaises(SystemExit) as caught:
            with self._cli(["-o", "string_value=bla", "-o", "int_value=hello"]):
                pass
        self.assertNotEqual(caught.exception.code, 0)
        self.assertEqual(self.config.root.int_value, 0)
        self.assertEqual(self.config.root.string_value, "")

    def test_config_assign_missing_assignment(self):
        with self.assertRaises(SystemExit) as caught:
            with self._cli(['-o', 'blap']):
                pass
        self.assertNotEqual(caught.exception.code, 0)


class PluginCommandLineArgumentsTest(OutputCaptureTest):

    def setUp(self):
        super(PluginCommandLineArgumentsTest, self).setUp()
        self.plugin = SampleCommandLinePlugin()
        plugins.manager.install(self.plugin)
        self.addCleanup(plugins.manager.uninstall, self.plugin)
        self._parser = cli_utils.SlashArgumentParser()

    def test_arguments_are_not_parsed_if_not_activated(self):
        args = ["--start-session-option", "2"]
        with self.assertRaises(SystemExit) as caught:
            self._parser.parse_args(args)
        assert caught.exception.code != 0

    def test_activation(self):
        cli_utils.add_pending_plugins_from_commandline(["--with-sample-plugin"])
        self.assertIn(self.plugin.get_name(), plugins.manager.get_future_active_plugins(), "plugin was not activated")

    def test_deactivation(self):
        argv = ["--without-sample-plugin"]
        plugins.manager.activate(self.plugin)
        argv = cli_utils.add_pending_plugins_from_commandline(argv)
        self.assertIn(self.plugin.get_name(), plugins.manager.get_active_plugins())
        assert argv == []
        plugins.manager.activate_pending_plugins()
        self.assertNotIn(self.plugin.get_name(), plugins.manager.get_future_active_plugins())
        self.assertNotIn(self.plugin.get_name(), plugins.manager.get_active_plugins())


    def test_argument_passing(self):
        argv = ["--with-sample-plugin", "--plugin-option", "value"]
        cli_utils.configure_arg_parser_by_plugins(self._parser)
        argv = cli_utils.add_pending_plugins_from_commandline(argv)
        parsed_args = self._parser.parse_args(argv)
        plugins.manager.activate_pending_plugins()
        cli_utils.configure_plugins_from_args(parsed_args)
        self.assertEqual(self.plugin.cmdline_param, "value")

    def test_help_shows_available_plugins(self):
        cli_utils.configure_arg_parser_by_plugins(self._parser)
        with self.assertRaises(SystemExit):
            self._parser.parse_args(['-h'])
        output = self.stdout.getvalue()
        self.assertIn("--with-sample-plugin", output)


class SampleCommandLinePlugin(PluginInterface):

    def get_name(self):
        return "sample-plugin"

    def configure_argument_parser(self, parser):
        parser.add_argument("--plugin-option")

    def configure_from_parsed_args(self, args):
        self.cmdline_param = args.plugin_option
