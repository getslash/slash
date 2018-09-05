# pylint: disable=redefined-outer-name
import pytest
from slash._compat import StringIO
from slash.frontend.slash_list_plugins import slash_list_plugins
from slash.plugins import manager, PluginInterface


def test_slash_list_plugins(report_stream):
    slash_list_plugins([], report_stream=report_stream)
    output = report_stream.getvalue()
    assert output
    installed = manager.get_installed_plugins()
    for plugin_name in installed:
        assert plugin_name in output


def test_slash_list_plugins_for_internal_plugins(report_stream):
    internal_plugin = InternalPlugin()
    manager.install(internal_plugin, is_internal=True)
    slash_list_plugins([], report_stream=report_stream)
    output = report_stream.getvalue()
    assert output

    assert internal_plugin.get_name() in manager.get_installed_plugins()
    assert internal_plugin.get_name() not in output
    assert '--internal-plugin-option' not in output


@pytest.fixture
def report_stream():
    return StringIO()


class InternalPlugin(PluginInterface):

    def get_name(self):
        return "internal plugin"

    def configure_argument_parser(self, parser):
        parser.add_argument("--internal-plugin-option")

    def configure_from_parsed_args(self, args):
        self.cmdline_param = args.plugin_option
