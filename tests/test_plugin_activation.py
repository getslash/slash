import re

import pytest

from slash import plugins
from slash import hooks
from slash.plugins import PluginInterface, IncompatiblePlugin
from .utils import CustomException


def test_get_active_plugins(plugin):
    plugins.manager.install(plugin)
    assert plugins.manager.get_active_plugins() == {}
    plugins.manager.activate(plugin)
    assert plugins.manager.get_active_plugins() == {plugin.get_name(): plugin}
    plugins.manager.deactivate(plugin)
    assert plugins.manager.get_active_plugins() == {}


def test_deactivaion_no_activation(plugin):
    plugins.manager.install(plugin)
    assert (not plugin._deactivate_called)
    plugins.manager.uninstall(plugin)
    assert not plugin._deactivate_called, 'Deactivate called even though plugin not activated'


def test_activation_exception(plugin):
    plugin.activate = CustomException.do_raise
    plugins.manager.install(plugin)

    with pytest.raises(CustomException):
        plugins.manager.activate(plugin)

    # make sure no registrations are in effect...
    _assert_hooks_not_registered(plugin)

    plugins.manager.deactivate(plugin)
    assert (not plugin._deactivate_called), 'Deactivate unexpectedly called!'


def test_deactivation_exception(plugin):
    plugin.deactivate = CustomException.do_raise
    plugins.manager.install(plugin, activate=True)

    with pytest.raises(CustomException):
        plugins.manager.deactivate(plugin)
    _assert_hooks_not_registered(plugin)


def test_activate_called(plugin):
    plugins.manager.install(plugin)
    assert (not plugin._activate_called)
    plugins.manager.activate(plugin)
    assert plugin._activate_called


def test_deactivate_called_on_deactivate(plugin):
    plugins.manager.install(plugin)
    assert (not plugin._deactivate_called)
    plugins.manager.activate(plugin)
    assert (not plugin._deactivate_called)
    plugins.manager.deactivate(plugin)
    assert plugin._deactivate_called


def test_hook_registration(plugin):
    plugins.manager.install(plugin)
    _assert_hooks_not_registered(plugin)
    plugins.manager.activate(plugin)
    hooks.session_start()
    assert plugin.session_start_call_count == 1
    plugins.manager.deactivate(plugin)
    hooks.session_start()
    assert plugin.session_start_call_count == 1


def test_install_and_activate(plugin):
    """test plugins.manager.install(..., activate=True)"""
    plugins.manager.install(plugin, activate=True)
    assert plugin.get_name() in plugins.manager.get_active_plugins()


def test_uninstall_also_deactivates(plugin):
    plugins.manager.install(plugin)
    plugins.manager.activate(plugin)
    plugins.manager.uninstall(plugin)
    hooks.session_start()
    assert plugin.session_start_call_count == 0


def test_cannot_activate_uninstalled_plugin():
    class Plugin(PluginInterface):

        def get_name(self):
            return "Test plugin"
    with pytest.raises(ValueError) as caught:
        plugins.manager.activate(Plugin())
    assert re.search(r".*not installed.*", str(caught.value))


def test_unknown_hook_names(request):
    "Make sure that plugins with unknown hook names get discarded"
    class Plugin(PluginInterface):

        def get_name(self):
            return "Test plugin"

        def unknown_hook_1(self):
            pass

    plugin = Plugin()
    plugins.manager.install(plugin)
    @request.addfinalizer
    def cleanup():
        plugins.manager.uninstall(plugin)

    with pytest.raises(IncompatiblePlugin) as caught:
        plugins.manager.activate(plugin)

    assert re.search(r"\bUnknown hooks\b.*", str(caught.value))


def test_custom_hook_names(request):
    "Make sure that plugins with unknown hook names get discarded"
    class Plugin(PluginInterface):

        def get_name(self):
            return "Test plugin"

        def custom_hook(self):
            pass

    hooks.add_custom_hook("custom_hook")
    @request.addfinalizer
    def cleanup():
        hooks.remove_custom_hook("custom_hook")
    plugin = Plugin()
    plugins.manager.install(plugin, activate=True)
    plugins.manager.uninstall(plugin)


def _assert_hooks_not_registered(plugin):
    hooks.session_start()
    assert plugin.session_start_call_count == 0, 'Hook unexpectedly registered!'


@pytest.fixture
def plugin(no_plugins):

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
    return StartSessionPlugin()
