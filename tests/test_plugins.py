# pylint: disable=unused-argument
import os

import gossip
import pytest
import slash
from slash._compat import PY2
from slash import hooks, plugins
from slash.plugins import IncompatiblePlugin, PluginInterface

from .utils import NamedPlugin



def test_registers_on_none(restore_plugins_on_cleanup, checkpoint):

    @slash.plugins.active  # pylint: disable=unused-variable
    class SamplePlugin(PluginInterface):

        def get_name(self):
            return 'sample'

        @plugins.registers_on(None)
        def some_method_here(self):
            checkpoint()

    gossip.trigger('slash.some_method_here')
    assert not checkpoint.called



def test_registers_on_with_private_methods(restore_plugins_on_cleanup, checkpoint):

    @slash.plugins.active  # pylint: disable=unused-variable
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
    @slash.plugins.active  # pylint: disable=unused-variable
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


@pytest.mark.parametrize('is_internal', [True, False])
def test_custom_hook_registration(request, is_internal):

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
    plugins.manager.install(p, activate=True, is_internal=is_internal)

    @request.addfinalizer
    def cleanup():              # pylint: disable=unused-variable
        plugins.manager.uninstall(p)

    registrations = gossip.get_hook(hook_name).get_registrations()
    assert len(registrations) == 1
    [r] = registrations
    if PY2:
        assert r.func.__func__ is MyPlugin.unknown.__func__  # pylint: disable=no-member
    else:
        assert r.func.__func__ is MyPlugin.unknown

    # make sure we deactivate properly as well
    plugins.manager.deactivate(p)
    assert not gossip.get_hook(hook_name).get_registrations()


def test_multiple_registers_on(request):
    hook_names = ['some_hook_{}'.format(i) for i in range(2)]

    class MyPlugin(PluginInterface):

        def get_name(self):
            return "plugin"

        @plugins.registers_on(hook_names[0])
        @plugins.registers_on(hook_names[1])
        def unknown(self):
            pass

    expected_func = MyPlugin.unknown.__func__ if PY2 else MyPlugin.unknown
    p = MyPlugin()
    plugins.manager.install(p, activate=True)
    @request.addfinalizer
    def cleanup():              # pylint: disable=unused-variable
        plugins.manager.uninstall(p)

    for hook_name in hook_names:
        registrations = gossip.get_hook(hook_name).get_registrations()
        assert len(registrations) == 1
        assert registrations[0].func.__func__ is expected_func

    plugins.manager.deactivate(p)

    for hook_name in hook_names:
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
    for hook_name, hook in hooks.get_all_hooks():  # pylint: disable=unused-variable
        for registration in hook.get_registrations():
            assert registration.token.startswith('slash.'), 'Callback {0} is not a builtin!'.format(hook.full_name)

def test_builtin_plugins_are_installed():
    installed = plugins.manager.get_installed_plugins()
    assert installed
    for filename in os.listdir(os.path.join(os.path.dirname(plugins.__file__), "builtin")):
        if filename.startswith("_") or filename.startswith(".") or not filename.endswith(".py"):
            continue
        assert filename[:(-3)] in installed


def test_get_installed_plugins():

    class CustomPlugin(PluginInterface):
        def __init__(self, name):
            super(CustomPlugin, self).__init__()
            self._name = name

        def get_name(self):
            return self._name

    some_plugin = CustomPlugin('some-plugin')
    internal_plugin = CustomPlugin('internal-plugin')
    plugins.manager.install(some_plugin)
    plugins.manager.install(internal_plugin, is_internal=True)

    assert some_plugin.get_name() in plugins.manager.get_installed_plugins(include_internals=True)
    assert some_plugin.get_name() in plugins.manager.get_installed_plugins(include_internals=False)
    assert internal_plugin.get_name() in plugins.manager.get_installed_plugins(include_internals=True)
    assert internal_plugin.get_name() not in plugins.manager.get_installed_plugins(include_internals=False)

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

    @slash.plugins.active  # pylint: disable=unused-variable
    class CustomPlugin(NamedPlugin):

        @slash.plugins.register_if(cond)
        def test_start(self):
            checkpoint()

    slash.hooks.test_start()  # pylint: disable=no-member

    assert checkpoint.called == cond


def test_register_if_nonexistent_hook(no_plugins, checkpoint):

    @slash.plugins.active  # pylint: disable=unused-variable
    class CustomPlugin(NamedPlugin):

        @slash.plugins.register_if(False)
        def nonexistent_hook(self):
            checkpoint()


def test_restoring_state_context():

    class Plugin1(NamedPlugin):
        pass

    @slash.plugins.active
    class Plugin2(NamedPlugin):
        pass

    class Plugin3(NamedPlugin):
        pass

    @slash.plugins.active
    class Plugin4(NamedPlugin):
        pass

    class Plugin5(NamedPlugin):
        pass


    manager = slash.plugins.manager
    manager.install(Plugin3())
    installed = manager.get_installed_plugins().copy()
    active = manager.get_active_plugins().copy()


    with manager.restoring_state_context():
        manager.install(Plugin1())
        manager.uninstall(Plugin2)
        manager.activate('Plugin3')
        manager.deactivate(Plugin4)
        manager.install(Plugin5(), activate=True)
        assert set(manager.get_installed_plugins()) == set(installed)\
            .union({'Plugin1', 'Plugin5'})\
            .difference({'Plugin2'})
        assert set(manager.get_active_plugins()) == set(active).union({'Plugin3', 'Plugin5'}).difference({'Plugin2', 'Plugin4'})
    assert manager.get_installed_plugins() == installed
    assert manager.get_active_plugins() == active
