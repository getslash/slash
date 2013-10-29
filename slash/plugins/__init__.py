import argparse
import os
from contextlib import contextmanager

from emport import import_file

from .. import hooks
from .._compat import iteritems, itervalues
from ..conf import config
from .interface import PluginInterface

_SKIPPED_PLUGIN_METHOD_NAMES = set(dir(PluginInterface))

class IncompatiblePlugin(ValueError):
    pass

class PluginManager(object):
    def __init__(self):
        super(PluginManager, self).__init__()
        self._installed = {}
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

    def install(self, plugin, activate=False):
        """
        Installs a plugin object to the plugin mechanism. ``plugin`` must be an object deriving from
        :class:`slash.plugins.interface.PluginInterface`.
        """
        if not isinstance(plugin, PluginInterface):
            raise IncompatiblePlugin("Invalid plugin type: {0!r}".format(type(plugin)))
        plugin_name = plugin.get_name()
        self._installed[plugin_name] = plugin
        if activate:
            self.activate(plugin_name)

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
        try:
            self.deactivate(plugin)
        except IncompatiblePlugin:
            pass
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
        for hook, callback in self._get_plugin_registrations(plugin):
            hook.register(callback, plugin_name)
        self._active.add(plugin_name)

    def deactivate(self, plugin):
        """
        Deactivates a plugin, unregistering all of its hook callbacks

        :param plugin: either a plugin object or a plugin name
        """
        plugin = self._get_installed_plugin(plugin)
        plugin_name = plugin.get_name()

        if plugin_name in self._active:
            for hook, _ in self._get_plugin_registrations(plugin):
                hook.unregister_by_identifier(plugin_name)
            self._active.discard(plugin_name)
            plugin.deactivate()

    def _get_installed_plugin(self, plugin):
        if isinstance(plugin, str):
            plugin_name = plugin
            plugin = self._installed[plugin_name]
        else:
            plugin_name = plugin.get_name()
        if self._installed.get(plugin_name) is not plugin:
            raise ValueError("Specified plugin is not installed!")
        return plugin

    def _get_plugin_registrations(self, plugin):
        returned = []
        unknown = []
        for hook_name in dir(type(plugin)):
            if hook_name in _SKIPPED_PLUGIN_METHOD_NAMES:
                continue
            if hook_name.startswith("_"):
                continue
            hook = getattr(hooks, hook_name, None)
            if hook is None:
                unknown.append(hook_name)
                continue
            assert hook is not None
            returned.append((hook, getattr(plugin, hook_name)))
        if unknown:
            raise IncompatiblePlugin("Unknown hooks: {0}".format(", ".join(unknown)))
        return returned

manager = PluginManager()
