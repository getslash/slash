import collections
import os
import sys

from emport import import_file
from sentinels import NOTHING
from vintage import warn_deprecation

import gossip
import gossip.hooks

from .. import hooks
from .._compat import itervalues, reraise
from ..conf import config
from ..utils.marks import mark, try_get_mark
from .interface import PluginInterface


_SKIPPED_PLUGIN_METHOD_NAMES = set(dir(PluginInterface))
RegistrationInfo = collections.namedtuple("RegistrationInfo", ("hook_name", "expect_exists"))
PluginInfo = collections.namedtuple("PluginInfo", ("plugin_instance", "is_internal"))

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

    def get_installed_plugins(self, include_internals=True):
        """
        Returns a dict mapping plugin names to currently installed plugins
        """
        return {plugin_name: plugin_info.plugin_instance
                for plugin_name, plugin_info in self._installed.items()
                if include_internals or (not plugin_info.is_internal)}

    def get_active_plugins(self):
        """
        Returns a dict mapping plugin names to currently active plugins
        """
        return dict(self._iterate_active_plugins())

    def _iterate_active_plugins(self):
        for active_name in self._active:
            yield (active_name, self._get_installed_plugin_instance_by_name(active_name))

    def get_future_active_plugins(self):
        """
        Returns a dictionary of plugins intended to be active once the 'pending activation' mechanism
        is finished
        """
        returned = self.get_active_plugins()
        for name in self._pending_activation:
            returned[name] = self.get_plugin(name)
        for name in self._pending_deactivation:
            returned.pop(name, None)
        return returned

    def get_plugin(self, plugin_name):
        """
        Retrieves a registered plugin by name, or raises a LookupError
        """
        return self._installed[plugin_name].plugin_instance

    def is_internal_plugin(self, plugin):
        """
        Returns rather installed plugin is internal plugin
        """
        plugin_name = plugin if isinstance(plugin, str) else plugin.get_name()
        return self._installed[plugin_name].is_internal

    def install(self, plugin, activate=False, activate_later=False, is_internal=False):
        """
        Installs a plugin object to the plugin mechanism. ``plugin`` must be an object deriving from
        :class:`slash.plugins.PluginInterface`.
        """
        if not isinstance(plugin, PluginInterface):
            raise IncompatiblePlugin("Invalid plugin type: {0!r}".format(type(plugin)))
        plugin_name = plugin.get_name()
        self._configure(plugin)
        self._installed[plugin_name] = PluginInfo(plugin, is_internal)
        if not hasattr(plugin, '__toggles__'):
            plugin.__toggles__ = {
                'session': gossip.Toggle(),
            }
        if activate:
            try:
                self.activate(plugin_name)
            except IncompatiblePlugin:
                exc_info = sys.exc_info()
                self.uninstall(plugin)
                reraise(*exc_info)
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
        for plugin_info in list(itervalues(self._installed)):
            self.uninstall(plugin_info.plugin_instance)
        assert not self._installed

    def activate(self, plugin):
        """
        Activates a plugin, registering its hook callbacks to their respective hooks.

        :param plugin: either a plugin object or a plugin name
        """
        plugin = self._get_installed_plugin(plugin)
        plugin_name = plugin.get_name()
        plugin.activate()
        for hook, callback, kwargs in self._get_plugin_registrations(plugin):
            hook.register(callback, **kwargs)
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
        token = self._get_token(plugin_name)

        if plugin_name in self._active:
            gossip.get_global_group().unregister_token(token)
            self._active.discard(plugin_name)
            plugin.deactivate()

    def _configure(self, plugin):
        cfg = plugin.get_config()
        if cfg is not None:
            warn_deprecation('PluginInterface.get_config() is deprecated. '
                             'Please use PluginInterface.get_default_config() instead')
        else:
            cfg = plugin.get_default_config()
        if cfg is not None:
            config['plugin_config'].extend({plugin.get_name(): cfg})

    def _unconfigure(self, plugin):
        plugin_config = config['plugin_config']
        if plugin.get_name() in plugin_config:
            plugin_config.pop(plugin.get_name())

    def _get_token(self, plugin_name):
        return "slash.plugins.{0}".format(plugin_name)

    def _get_installed_plugin_instance_by_name(self, plugin_name):
        plugin_info = self._installed.get(plugin_name)
        if plugin_info is None:
            return None
        return plugin_info.plugin_instance

    def _get_installed_plugin(self, plugin):
        if isinstance(plugin, str):
            plugin_name = plugin
            plugin = self._get_installed_plugin_instance_by_name(plugin_name)
        else:
            plugin_name = plugin.get_name()
        if plugin is None or self._get_installed_plugin_instance_by_name(plugin_name) is not plugin:
            raise UnknownPlugin("Unknown plugin: {0}".format(plugin_name))
        return plugin

    def _get_plugin_registrations(self, plugin):
        plugin_name = plugin.get_name()
        returned = []
        unknown = []
        global_needs = try_get_mark(plugin, 'plugin_needs', [])
        global_provides = try_get_mark(plugin, 'plugin_provides', [])

        has_session_end = has_session_start = False

        register_no_op_hooks = set()
        if global_provides:
            register_no_op_hooks.update(hook.full_name for hook in gossip.get_group('slash').get_hooks())

        for method_name in dir(type(plugin)):
            if method_name in _SKIPPED_PLUGIN_METHOD_NAMES:
                continue

            method = getattr(plugin, method_name)

            if not hasattr(method, '__call__'):
                continue

            registration_list = try_get_mark(method, 'register_on', NOTHING)

            if registration_list is not NOTHING:
                registration_list = [RegistrationInfo(hook_name, False) for hook_name in registration_list]
            else:
                if method_name.startswith('_'):
                    continue
                registration_list = [RegistrationInfo("slash.{0}".format(method_name), True)]

            for registration_info in registration_list:
                if registration_info.hook_name is None:
                    # asked not to register for nothing
                    continue

                if not try_get_mark(method, 'register_if', True):
                    continue

                plugin_needs = try_get_mark(method, 'plugin_needs', []) + global_needs
                plugin_provides = try_get_mark(method, 'plugin_provides', []) + global_provides

                try:
                    if registration_info.expect_exists:
                        hook = gossip.get_hook(registration_info.hook_name)
                    else:
                        hook = gossip.hooks.get_or_create_hook(registration_info.hook_name)
                        if not hook.is_defined() and hook.group.is_strict():
                            raise LookupError()
                except LookupError:
                    unknown.append(registration_info.hook_name)
                    continue

                assert hook is not None
                register_no_op_hooks.discard(registration_info.hook_name)

                kwargs = {
                    'needs': plugin_needs,
                    'provides': plugin_provides,
                    'token': self._get_token(plugin_name),
                }
                if registration_info.hook_name == 'slash.session_start':
                    has_session_start = True
                    kwargs['toggles_on'] = plugin.__toggles__['session']
                elif registration_info.hook_name == 'slash.session_end':
                    has_session_end = True
                    kwargs['toggles_off'] = plugin.__toggles__['session']

                returned.append((hook, method, kwargs))

        if has_session_end and not has_session_start:
            hook = gossip.get_hook('slash.session_start')
            returned.append((hook, lambda: None, {'toggles_on': plugin.__toggles__['session']}))
            register_no_op_hooks.discard(hook.full_name)

        for hook_name in register_no_op_hooks:
            hook = gossip.get_hook(hook_name)
            hook.register_no_op(provides=global_provides, token=self._get_token(plugin_name))

        if unknown:
            raise IncompatiblePlugin("Unknown hooks: {0}".format(", ".join(unknown)))
        return returned


manager = PluginManager()

def registers_on(hook_name):
    """Marks the decorated plugin method to register on a custom hook, rather than
    the method name in the 'slash' group, which is the default behavior for plugins

    Specifying ``registers_on(None)`` means that this is not a hook entry point at all.
    """
    return mark("register_on", hook_name, append=True)

def register_if(condition):
    """Marks the decorated plugins method to only be registered if *condition* is ``True``
    """
    return mark("register_if", condition)

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
