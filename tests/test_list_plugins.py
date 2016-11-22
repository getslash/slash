from slash.frontend.slash_list_plugins import slash_list_plugins
from slash.plugins import manager
from slash._compat import StringIO


def test_slash_list_plugins():
    report_stream = StringIO()

    slash_list_plugins([], report_stream=report_stream)
    output = report_stream.getvalue()
    assert output
    installed = manager.get_installed_plugins()
    for plugin_name in installed:
        assert plugin_name in output
