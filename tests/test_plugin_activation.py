# pylint: disable=superfluous-parens,protected-access
import re

import pytest

from slash import plugins
from slash import hooks
from slash.plugins import PluginInterface, IncompatiblePlugin, UnknownPlugin
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
    hooks.session_start()  # pylint: disable=no-member
    assert plugin.session_start_call_count == 1
    plugins.manager.deactivate(plugin)
    hooks.session_start()  # pylint: disable=no-member
    assert plugin.session_start_call_count == 1


def test_install_and_activate(plugin):
    """test plugins.manager.install(..., activate=True)"""
    plugins.manager.install(plugin, activate=True)
    assert plugin.get_name() in plugins.manager.get_active_plugins()


def test_uninstall_also_deactivates(plugin):
    plugins.manager.install(plugin)
    plugins.manager.activate(plugin)
    plugins.manager.uninstall(plugin)
    hooks.session_start()  # pylint: disable=no-member
    assert plugin.session_start_call_count == 0


def test_cannot_activate_uninstalled_plugin():
    class Plugin(PluginInterface):

        def get_name(self):
            return "Test plugin"
    with pytest.raises(ValueError) as caught:
        plugins.manager.activate(Plugin())
    assert re.search(r".*Unknown plugin: Test plugin.*", str(caught.value))


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
    def cleanup():  # pylint: disable=unused-variable
        plugins.manager.uninstall(plugin)

    with pytest.raises(IncompatiblePlugin) as caught:
        plugins.manager.activate(plugin)

    assert re.search(r"\bUnknown hooks\b.*", str(caught.value))


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_custom_hook_names(request):
    "Make sure that plugins with unknown hook names get discarded"
    class Plugin(PluginInterface):

        def get_name(self):
            return "Test plugin"

        def custom_hook(self):
            pass

    hooks.add_custom_hook("custom_hook")

    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        hooks.remove_custom_hook("custom_hook")
    plugin = Plugin()
    plugins.manager.install(plugin, activate=True)
    plugins.manager.uninstall(plugin)


def test_pending_activation(plugin):
    plugins.manager.install(plugin)
    assert not plugins.manager.get_active_plugins()
    plugins.manager.activate_later(plugin)
    assert not plugins.manager.get_active_plugins()
    plugins.manager.activate_pending_plugins()
    assert plugin.get_name() in plugins.manager.get_active_plugins()
    assert plugin._activate_called


def test_pending_activation_deactivation(plugin):
    plugins.manager.install(plugin)
    plugins.manager.activate_later(plugin)
    plugins.manager.deactivate_later(plugin)
    assert plugin.get_name() in plugins.manager._pending_activation
    assert plugin.get_name() in plugins.manager._pending_deactivation
    plugins.manager.activate_pending_plugins()
    assert not plugin._activate_called


def test_install_activate_later(plugin):
    plugins.manager.install(plugin, activate_later=True)
    assert plugin.get_name() in plugins.manager._pending_activation


@pytest.mark.parametrize('activate_later_first', [True, False])
def test_deactivate_later_already_activated(plugin, activate_later_first):
    plugins.manager.install(plugin, activate=True)
    if activate_later_first:
        plugins.manager.activate_later(plugin)
    plugins.manager.deactivate_later(plugin)
    plugins.manager.activate_pending_plugins()
    assert plugin.get_name() not in plugins.manager.get_active_plugins()
    assert plugin._activate_called
    assert plugin._deactivate_called

def test_pending_activation_not_exists(plugin):
    with pytest.raises(UnknownPlugin):
        plugins.manager.activate_later(plugin)
    with pytest.raises(UnknownPlugin):
        plugins.manager.activate_later(plugin.get_name())



def test_pending_deactivation_not_exists(plugin):
    with pytest.raises(UnknownPlugin):
        plugins.manager.deactivate_later(plugin)
    with pytest.raises(UnknownPlugin):
        plugins.manager.deactivate_later(plugin.get_name())



def _assert_hooks_not_registered(plugin):
    hooks.session_start()  # pylint: disable=no-member
    assert plugin.session_start_call_count == 0, 'Hook unexpectedly registered!'
