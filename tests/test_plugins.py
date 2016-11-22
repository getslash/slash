#pylint: disable=unused-argument
import os

import gossip
import pytest
import slash
from slash._compat import PY2
from slash import hooks, plugins
from slash.plugins import IncompatiblePlugin, PluginInterface

from .utils import CustomException, NamedPlugin



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


def test_custom_hook_registration(request):

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

    @request.addfinalizer
    def cleanup():              # pylint: disable=unused-variable
        plugins.manager.uninstall(p)

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

    assert set(plugins.manager.get_installed_plugins()) == set(initially_installed)


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


def test_cannot_install_incompatible_subclasses(no_plugins):

    class Incompatible(object):
        pass
    for invalid in (Incompatible, Incompatible(), PluginInterface, object(), 1, "string"):
        with pytest.raises(IncompatiblePlugin):
            plugins.manager.install(invalid)
    assert plugins.manager.get_installed_plugins() == {}


def test_install_uninstall(no_plugins):
    plugin_name = "some_plugin_name"

    class CustomPlugin(PluginInterface):

        def get_name(self):
            return plugin_name
    with pytest.raises(LookupError):
        plugins.manager.get_plugin(plugin_name)
    plugin = CustomPlugin()
    plugins.manager.install(plugin)
    assert plugins.manager.get_plugin(plugin_name) is plugin
    plugins.manager.uninstall(plugin)
    with pytest.raises(LookupError):
        plugins.manager.get_plugin(plugin_name)



@pytest.mark.parametrize('cond', [True, False])
def test_register_if(no_plugins, checkpoint, cond):

    @slash.plugins.active
    class CustomPlugin(NamedPlugin):

        @slash.plugins.register_if(cond)
        def test_start(self):
            checkpoint()

    slash.hooks.test_start()

    assert checkpoint.called == cond


def test_register_if_nonexistent_hook(no_plugins, checkpoint):

    @slash.plugins.active
    class CustomPlugin(NamedPlugin):

        @slash.plugins.register_if(False)
        def nonexistent_hook(self):
            checkpoint()
