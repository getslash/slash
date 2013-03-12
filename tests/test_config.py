from .utils import TestCase
from confetti import Config
from shakedown.conf import config
from shakedown.utils import conf_utils

class ArgumentParsingTest(TestCase):
    def setUp(self):
        super(ArgumentParsingTest, self).setUp()
        self.config = Config({
            "a": {"a1": {"flag1": True // conf_utils.Cmdline(off="--no-flag1")}},
            "b": {"b1": {"flag2": False // conf_utils.Cmdline(on="--flag2")}},
            })

    def test__config_off_flag(self):
        with conf_utils.get_parsed_config_args_context(self.config, ["--no-flag1"]) as argv:
            self.assertFalse(self.config["a"]["a1"]["flag1"])
        self.assertTrue(self.config["a"]["a1"]["flag1"])

    def test__config_on_flag(self):
        with conf_utils.get_parsed_config_args_context(self.config, ["--flag2"]) as argv:
            self.assertTrue(self.config["b"]["b1"]["flag2"])
        self.assertFalse(self.config["b"]["b1"]["flag2"])
