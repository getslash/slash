import collections
import gossip
import itertools
import os
import re
import sys
from .interface import PluginInterface
from .registration_info import RegistrationInfo
from .._compat import itervalues, reraise
from ..utils.marks import try_get_mark
from ..utils import parallel_utils
from ..conf import config
from contextlib import contextmanager
from emport import import_file
from sentinels import NOTHING
from vintage import warn_deprecation
import logbook

_logger = logbook.Logger(__name__)

_SKIPPED_PLUGIN_METHOD_NAMES = set(dir(PluginInterface))
PluginInfo = collections.namedtuple("PluginInfo", ("plugin_instance", "is_internal"))
_DEPRECATED_CHARACTERS = '-_'

class IncompatiblePlugin(ValueError):
    pass

class UnknownPlugin(ValueError):
    pass

class IllegalPluginName(ValueError):
    pass

class PluginManager(object):
    def __init__(self):
        super(PluginManager, self).__init__()
        self._installed = {}
        self._cmd_line_to_name = {}
        self._config_to_name = {}
        self._pending_activation = set()
        self._pending_deactivation = set()
        self._active = set()
        self.install_builtin_plugins()

    @contextmanager
    def restoring_state_context(self):
        previous_installed = self._installed.copy()
        previous_active = {name: self._installed[name] for name in self._active}
        try:
            yield
        finally:
            for name in set(previous_installed) - set(self._installed):
                self.install(previous_installed[name].plugin_instance)
            for name in set(previous_active) - self._active:
                self.activate(name)
            for name in self._active - set(previous_active):
                self.deactivate(name)
            for name in set(self._installed) - set(previous_installed):
                self.uninstall(name)


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

    def _is_parallel_supported(self, plugin):
        if not parallel_utils.is_parallel_session():
            return False
        plugin_parallel_mode = try_get_mark(plugin, 'parallel_mode', parallel_utils.ParallelPluginModes.ENABLED)
        if plugin_parallel_mode == parallel_utils.ParallelPluginModes.ENABLED:
            return False
        if (plugin_parallel_mode == parallel_utils.ParallelPluginModes.DISABLED) \
            or (plugin_parallel_mode == parallel_utils.ParallelPluginModes.PARENT_ONLY and parallel_utils.is_child_session()) \
            or (plugin_parallel_mode == parallel_utils.ParallelPluginModes.CHILD_ONLY and parallel_utils.is_parent_session()):
            return True
        return False

    def configure_for_parallel_mode(self):
        for plugin in self.get_installed_plugins().values():
            if self._is_parallel_supported(plugin):
                self.deactivate_later(plugin)

    def install(self, plugin, activate=False, activate_later=False, is_internal=False):
        """
        Installs a plugin object to the plugin mechanism. ``plugin`` must be an object deriving from
        :class:`slash.plugins.PluginInterface`.
        """
        if not isinstance(plugin, PluginInterface):
            raise IncompatiblePlugin("Invalid plugin type: {!r}".format(type(plugin)))
        plugin_name = plugin.get_name()
        if re.search(r'[^A-Za-z0-9_ -]', plugin_name):
            raise IllegalPluginName("Illegal plugin name: {}".format(plugin_name))

        if any(char in plugin_name for char in _DEPRECATED_CHARACTERS):
            warn_deprecation("In the future, dashes and underscore will not be allowed in plugin names - "
                             "spaces should be used instead (plugin name: {!r})".format(plugin_name))
        self._configure(plugin)
        self._installed[plugin_name] = PluginInfo(plugin, is_internal)
        self._cmd_line_to_name[self.normalize_command_line_name(plugin_name)] = plugin_name
        self._config_to_name[self.normalize_config_name(plugin_name)] = plugin_name
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
                "slash.plugins.builtin.{}".format(builtin_plugin_module),
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
        plugin_name = plugin.get_name()
        self._installed.pop(plugin_name)
        cmd_name = self.normalize_command_line_name(plugin_name)
        self._cmd_line_to_name.pop(cmd_name, None)
        config_name = self.normalize_config_name(plugin_name)
        self._config_to_name.pop(config_name, None)

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
        if self._is_parallel_supported(plugin):
            _logger.warn("Activating plugin {} though it's configuration for parallel mode doesn't fit to current session".format(plugin.get_name()))
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

    def normalize_command_line_name(self, plugin_name):
        return plugin_name.replace(' ', '-')

    def normalize_config_name(self, plugin_name):
        return plugin_name.replace(' ', '_')

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
            plugin_name = plugin.get_name()
            config_name = self.normalize_config_name(plugin_name)
            config['plugin_config'].extend({config_name: cfg})

    def _unconfigure(self, plugin):
        plugin_config = config['plugin_config']
        config_name = self.normalize_config_name(plugin.get_name())
        if config_name in plugin_config:
            plugin_config.pop(config_name)

    def _get_token(self, plugin_name):
        return "slash.plugins.{}".format(plugin_name)

    def _get_installed_plugin_instance_by_name(self, plugin_name):
        plugin_info = self._installed.get(plugin_name)
        if plugin_info is None:
            return None
        return plugin_info.plugin_instance

    def _get_installed_plugin_instance_by_type(self, plugin_class):
        for plugin in self._installed.values():
            if type(plugin.plugin_instance) is plugin_class: # pylint: disable=unidiomatic-typecheck
                return plugin.plugin_instance
        return None

    def _get_installed_plugin(self, plugin):
        if isinstance(plugin, str):
            plugin_name = plugin
            if plugin_name in self._cmd_line_to_name:
                plugin_name = self._cmd_line_to_name[plugin_name]
            plugin_instance = self._get_installed_plugin_instance_by_name(plugin_name)
        elif isinstance(plugin, type):
            plugin_instance = self._get_installed_plugin_instance_by_type(plugin)
            plugin_name = plugin_instance.get_name() if plugin_instance is not None else repr(plugin)
        else:
            plugin_instance = plugin
            plugin_name = plugin.get_name()
        if plugin_instance is None or self._get_installed_plugin_instance_by_name(plugin_name) is not plugin_instance:
            raise UnknownPlugin("Unknown plugin: {}".format(plugin_name))
        return plugin_instance

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
                registration_list = registration_list[:]
            else:
                if method_name.startswith('_'):
                    continue
                registration_list = [RegistrationInfo("slash.{}".format(method_name), expect_exists=True)]

            for registration_info in registration_list:
                if registration_info.hook_name is None:
                    # asked not to register for nothing
                    continue

                if not try_get_mark(method, 'register_if', True):
                    continue

                plugin_needs = list(
                    itertools.chain(
                        try_get_mark(method, 'plugin_needs', []),
                        global_needs,
                        registration_info.register_kwargs.get('needs', [])))

                plugin_provides = list(
                    itertools.chain(
                        try_get_mark(method, 'plugin_provides', []),
                        global_provides,
                        registration_info.register_kwargs.get('provides', [])))

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

                kwargs = registration_info.register_kwargs.copy()
                kwargs.update({
                    'needs': plugin_needs,
                    'provides': plugin_provides,
                    'token': self._get_token(plugin_name),
                })
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
            raise IncompatiblePlugin("Unknown hooks: {}".format(", ".join(unknown)))
        return returned


manager = PluginManager()
