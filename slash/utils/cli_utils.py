from .. import conf
from .. import plugins
from .formatter import Formatter
import argparse
from contextlib import contextmanager
from .._compat import iteritems, itervalues, cStringIO
import sys

@contextmanager
def get_cli_environment_context(argv=None, config=conf.config, extra_args=(), allow_unknown_args=False):
    if argv is None:
        argv = sys.argv[1:]
    parser = PluginAwareArgumentParser()
    if extra_args:
        _populate_extra_args(parser, extra_args)
    argv = list(argv) # copy the arguments, as we'll be gradually removing known arguments
    with _get_active_plugins_context(argv):
        _configure_parser_by_active_plugins(parser)
        _configure_parser_by_config(parser, config)
        if allow_unknown_args:
            parsed_args, remainder = parser.parse_known_args(argv)
        else:
            parsed_args = parser.parse_args(argv)
            remainder = []
        parsed_args.remainder = remainder
        _configure_plugins_from_args(parsed_args)
        with _get_modified_configuration_from_args_context(parser, config, parsed_args):
            yield parser, parsed_args

def _populate_extra_args(parser, extra_args):
    for argument in extra_args:
        parser.add_argument(*argument.args, **argument.kwargs)

@contextmanager
def _get_active_plugins_context(argv):
    cleanups = []
    prev_active = set(plugins.manager.get_active_plugins())
    try:
        new_active, new_argv = _get_new_active_plugins_from_args(argv)
        for plugin_name in new_active - prev_active:
            plugins.manager.activate(plugin_name)
            cleanups.append((plugins.manager.deactivate, plugin_name))
        for plugin_name in prev_active - new_active:
            plugins.manager.deactivate(plugin_name)
            cleanups.append((plugins.manager.activate, plugin_name))
        del argv[:]
        argv.extend(new_argv)
        yield
    finally:
        for cleanup_func, plugin_name in reversed(cleanups):
            cleanup_func(plugin_name)

_PLUGIN_ACTIVATION_PREFIX = "--with-"
_PLUGIN_DEACTIVATION_PREFIX = "--without-"
def _get_new_active_plugins_from_args(argv):
    new_active = set(plugins.manager.get_active_plugins())
    returned_argv = []
    for arg in argv:
        if arg.startswith(_PLUGIN_DEACTIVATION_PREFIX):
            new_active.discard(arg[len(_PLUGIN_DEACTIVATION_PREFIX):])
        elif arg.startswith(_PLUGIN_ACTIVATION_PREFIX):
            new_active.add(arg[len(_PLUGIN_ACTIVATION_PREFIX):])
        else:
            returned_argv.append(arg)
    return new_active, returned_argv

def _configure_parser_by_active_plugins(parser):
    for plugin in itervalues(plugins.manager.get_active_plugins()):
        plugin.configure_argument_parser(parser)

def _configure_plugins_from_args(args):
    for plugin in itervalues(plugins.manager.get_active_plugins()):
        plugin.configure_from_parsed_args(args)

def _configure_parser_by_config(parser, config):
    parser.add_argument(
        "-o", dest="config_overrides", metavar="PATH=VALUE", action="append",
        default=[],
        help="Provide overrides for configuration"
    )
    for path, node, cmdline in _iter_cmdline_config(config):
        cmdline.configure_parser(parser, path, node)

def _iter_cmdline_config(config):
    for path, cfg in config.traverse_leaves():
        cmdline = (cfg.metadata or {}).get("cmdline")
        if cmdline is None:
            continue
        yield path, cfg, cmdline

@contextmanager
def _get_modified_configuration_from_args_context(parser, config, args):
    to_restore = []
    try:
        for path, cfg, cmdline in _iter_cmdline_config(config):
            old_value = cfg.get_value()
            new_value = cmdline.update_value(old_value, args)
            if new_value != old_value:
                to_restore.append((path, cfg.get_value()))
                config.assign_path(path, new_value)
        for override in args.config_overrides:
            if "=" not in override:
                parser.error("Invalid config override: {0}".format(override))
            path, _ = override.split("=", 1)
            to_restore.append((path, config.get_path(path)))
            try:
                config.assign_path_expression(override, deduce_type=True, default_type=str)
            except ValueError:
                parser.error("Invalid value for config override: {0}".format(override))
        yield
    finally:
        for path, prev_value in reversed(to_restore):
            config.assign_path(path, prev_value)

class PluginAwareArgumentParser(argparse.ArgumentParser):
    def format_help(self):
        returned = cStringIO()
        returned.write(super(PluginAwareArgumentParser, self).format_help())
        f = Formatter(returned)
        for index, (plugin_name, plugin) in enumerate(self._iter_available_plugins()):
            if index == 0:
                f.writeln()
                f.writeln("Available (inactive) plugins:")
                f.indent()
            f.write(_PLUGIN_ACTIVATION_PREFIX + plugin_name)
            description = plugin.get_description()
            if description is not None:
                f.writeln()
                with f.indented(2):
                    f.write(description)
            f.writeln()
        return returned.getvalue()

    def _iter_available_plugins(self):
        active_plugin_names = set(plugins.manager.get_active_plugins())
        for plugin_name, plugin in iteritems(plugins.manager.get_installed_plugins()):
            if plugin_name not in active_plugin_names:
                yield plugin_name, plugin

class Argument(object):
    """
    helper to defer initialization of cmdline parsers to later stages
    """
    def __init__(self, *args, **kwargs):
        super(Argument, self).__init__()
        self.args = args
        self.kwargs = kwargs
