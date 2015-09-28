import os

from emport import import_file
from sentinels import NOTHING

import gossip
import gossip.hooks

from .. import hooks
from .._compat import itervalues
from ..conf import config
from ..utils.marks import mark, try_get_mark
from .interface import PluginInterface


_SKIPPED_PLUGIN_METHOD_NAMES = set(dir(PluginInterface))

class IncompatiblePlugin(ValueError):
    pass

class UnknownPlugin(ValueError):
    pass

class PluginManager(object):
    def __init__(self):
        super(PluginManager, self).__init__()
        self._installed = {}
        self._pending_activation = set()
        self._pending_deactivation = set()
        self._active = set()
        self.install_builtin_plugins()

    def discover(self):
        """
        Iterates over all search paths and loads plugins
        """
        for search_path in config.root.plugins.search_paths:
            for path, _, filenames in os.walk(search_path):
                for filename in filenames:
                    if not filename.endswith(".py"):
                        continue
                    module = import_file(os.path.join(path, filename))
                    install_func = getattr(module, "install_plugins", None)
                    if install_func is None:
                        continue
                    install_func()

    def get_installed_plugins(self):
        """
        Returns a dict mapping plugin names to currently installed plugins
        """
        return self._installed.copy()

    def get_active_plugins(self):
        """
        Returns a dict mapping plugin names to currently active plugins
        """
        return dict(self._iterate_active_plugins())

    def _iterate_active_plugins(self):
        for active_name in self._active:
            yield (active_name, self._installed[active_name])

    def get_plugin(self, plugin_name):
        """
        Retrieves a registered plugin by name, or raises a LookupError
        """
        return self._installed[plugin_name]

    def install(self, plugin, activate=False, activate_later=False):
        """
        Installs a plugin object to the plugin mechanism. ``plugin`` must be an object deriving from
        :class:`slash.plugins.PluginInterface`.
        """
        if not isinstance(plugin, PluginInterface):
            raise IncompatiblePlugin("Invalid plugin type: {0!r}".format(type(plugin)))
        plugin_name = plugin.get_name()
        self._configure(plugin)
        self._installed[plugin_name] = plugin
        if activate:
            self.activate(plugin_name)
        if activate_later:
            self.activate_later(plugin_name)

    def install_builtin_plugins(self):
        for builtin_plugin_module in self._iter_builtin_plugin_modules():
            module = __import__(
                "slash.plugins.builtin.{0}".format(builtin_plugin_module),
                fromlist=[""]
            )
            self.install(module.Plugin())

    def _iter_builtin_plugin_modules(self):
        builtin_dir = os.path.join(os.path.dirname(__file__), "builtin")
        for filename in os.listdir(builtin_dir):
            if filename.startswith("_") or filename.startswith(".") or not filename.endswith(".py"):
                continue
            yield filename[:-3]

    def uninstall(self, plugin):
        """
        Uninstalls a plugin
        """
        plugin = self._get_installed_plugin(plugin)
        try:
            self.deactivate(plugin)
        except IncompatiblePlugin:
            pass
        self._unconfigure(plugin)
        self._installed.pop(plugin.get_name())

    def uninstall_all(self):
        """
        Uninstalls all installed plugins
        """
        for plugin in list(itervalues(self._installed)):
            self.uninstall(plugin)

    def activate(self, plugin):
        """
        Activates a plugin, registering its hook callbacks to their respective hooks.

        :param plugin: either a plugin object or a plugin name
        """
        plugin = self._get_installed_plugin(plugin)
        plugin_name = plugin.get_name()
        plugin.activate()
        for hook, callback, plugin_needs, plugin_provides in self._get_plugin_registrations(plugin):
            hook.register(callback, token=self._get_token(plugin_name), needs=plugin_needs, provides=plugin_provides)
        self._active.add(plugin_name)

    def activate_later(self, plugin):
        """
        Adds a plugin to the set of plugins pending activation. It can be remvoed from the queue with :meth:`.deactivate_later`

        .. seealso:: :meth:`.activate_pending_plugins`
        """
        self._pending_activation.add(self._get_installed_plugin(plugin).get_name())

    def deactivate_later(self, plugin):
        """
        Removes a plugin from the set of plugins pending activation.

        .. seealso:: :meth:`.activate_pending_plugins`
        """

        self._pending_deactivation.add(self._get_installed_plugin(plugin).get_name())

    def activate_pending_plugins(self):
        """
        Activates all plugins queued with :meth:`.activate_later`
        """
        while self._pending_activation:
            plugin_name = self._pending_activation.pop()
            if plugin_name not in self._pending_deactivation:
                self.activate(plugin_name)

        while self._pending_deactivation:
            plugin_name = self._pending_deactivation.pop()
            if plugin_name in self._active:
                self.deactivate(plugin_name)

    def deactivate(self, plugin):
        """
        Deactivates a plugin, unregistering all of its hook callbacks

        :param plugin: either a plugin object or a plugin name
        """
        plugin = self._get_installed_plugin(plugin)
        plugin_name = plugin.get_name()

        if plugin_name in self._active:
            gossip.get_global_group().unregister_token(self._get_token(plugin_name))
            self._active.discard(plugin_name)
            plugin.deactivate()

    def _configure(self, plugin):
        cfg = plugin.get_config()
        if cfg is not None:
            config['plugin_config'].extend({plugin.get_name(): cfg})

    def _unconfigure(self, plugin):
        plugin_config = config['plugin_config']
        if plugin.get_name() in plugin_config:
            plugin_config.pop(plugin.get_name())

    def _get_token(self, plugin_name):
        return "slash.plugins.{0}".format(plugin_name)

    def _get_installed_plugin(self, plugin):
        if isinstance(plugin, str):
            plugin_name = plugin
            plugin = self._installed.get(plugin_name)
        else:
            plugin_name = plugin.get_name()
        if plugin is None or self._installed.get(plugin_name) is not plugin:
            raise UnknownPlugin("Unknown plugin: {0}".format(plugin_name))
        return plugin

    def _get_plugin_registrations(self, plugin):
        returned = []
        unknown = []
        global_needs = try_get_mark(plugin, 'plugin_needs', [])
        global_provides = try_get_mark(plugin, 'plugin_provides', [])
        for method_name in dir(type(plugin)):
            if method_name in _SKIPPED_PLUGIN_METHOD_NAMES:
                continue

            method = getattr(plugin, method_name)

            if not hasattr(method, '__call__'):
                continue

            hook_name = try_get_mark(method, 'register_on', NOTHING)

            if hook_name is None:
                # asked not to register for nothing
                continue

            if hook_name is not NOTHING:
                expect_exists = False
            else:
                if method_name.startswith('_'):
                    continue
                expect_exists = True
                hook_name = "slash.{0}".format(method_name)

            plugin_needs = try_get_mark(method, 'plugin_needs', []) + global_needs
            plugin_provides = try_get_mark(method, 'plugin_provides', []) + global_provides

            try:
                if expect_exists:
                    hook = gossip.get_hook(hook_name)
                else:
                    hook = gossip.hooks.get_or_create_hook(hook_name)
                    if not hook.is_defined() and hook.group.is_strict():
                        raise LookupError()
            except LookupError:
                unknown.append(hook_name)
                continue
            assert hook is not None
            returned.append((hook, method, plugin_needs, plugin_provides))
        if unknown:
            raise IncompatiblePlugin("Unknown hooks: {0}".format(", ".join(unknown)))
        return returned

manager = PluginManager()

def registers_on(hook_name):
    """Marks the decorated plugin method to register on a custom hook, rather than
    the method name in the 'slash' group, which is the default behavior for plugins

    Specifying ``registers_on(None)`` means that this is not a hook entry point at all.
    """
    return mark("register_on", hook_name)

def active(plugin_class):
    """Decorator for automatically installing and activating a plugin upon definition
    """
    plugin = plugin_class()
    manager.install(plugin)
    manager.activate(plugin)

    return plugin_class

def needs(what):
    return mark("plugin_needs", what, append=True)


def provides(what):
    return mark("plugin_provides", what, append=True)
