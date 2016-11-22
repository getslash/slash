from __future__ import print_function
import argparse
import os
import sys
from contextlib import contextmanager

import colorama

from .. import conf, plugins, hooks
from .._compat import cStringIO, iteritems, itervalues
from ..plugins import UnknownPlugin


@contextmanager
def get_cli_environment_context(argv=None, config=conf.config, extra_args=(), positionals_metavar=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = SlashArgumentParser(prog=_deduce_program_name(), positionals_metavar=positionals_metavar)
    if extra_args:
        _populate_extra_args(parser, extra_args)
    _configure_parser_by_plugins(parser)
    _configure_parser_by_config(parser, config)

    try:
        argv = _add_pending_plugins_from_commandline(argv)
    except UnknownPlugin as e:
        parser.error(str(e))

    if positionals_metavar is not None:
        parsed_args, positionals = parser.parse_known_args(argv)
    else:
        parsed_args = parser.parse_args(argv)
        positionals = []

    with _get_modified_configuration_from_args_context(parser, config, parsed_args):
        hooks.configure() # pylint: disable=no-member
        plugins.manager.activate_pending_plugins()
        parsed_args.positionals = positionals
        _configure_plugins_from_args(parsed_args)
        yield parser, parsed_args

def _deduce_program_name():
    returned = os.path.basename(sys.argv[0])
    if len(sys.argv) > 1:
        returned += " {0}".format(sys.argv[1])
    return returned

def _populate_extra_args(parser, extra_args):
    for argument in extra_args:
        parser.add_argument(*argument.args, **argument.kwargs)

_PLUGIN_ACTIVATION_PREFIX = "--with-"
_PLUGIN_DEACTIVATION_PREFIX = "--without-"
def _add_pending_plugins_from_commandline(argv):
    returned_argv = []
    for arg in argv:
        if arg.startswith(_PLUGIN_DEACTIVATION_PREFIX):
            plugin_name = arg[len(_PLUGIN_DEACTIVATION_PREFIX):]
            plugins.manager.deactivate_later(plugin_name)
        elif arg.startswith(_PLUGIN_ACTIVATION_PREFIX):
            plugin_name = arg[len(_PLUGIN_ACTIVATION_PREFIX):]
            plugins.manager.activate_later(plugin_name)
        else:
            returned_argv.append(arg)
    return returned_argv

def _configure_parser_by_plugins(parser):
    for plugin in itervalues(plugins.manager.get_installed_plugins()):
        group = parser.add_argument_group('Options for --with-{0}'.format(plugin.get_name()))
        plugin.configure_argument_parser(group)

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
                config.assign_path(path, new_value, deduce_type=True, default_type=str)
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

class SlashArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        positionals_metavar = kwargs.pop("positionals_metavar", None)
        super(SlashArgumentParser, self).__init__(*args, **kwargs)
        self._positionals_metavar = positionals_metavar


    def format_help(self):
        returned = cStringIO()
        helpstring = super(SlashArgumentParser, self).format_help()
        helpstring = self._tweak_usage_positional_metavars(helpstring)
        returned.write(helpstring)
        return returned.getvalue()

    def _tweak_usage_positional_metavars(self, usage):
        """
        Adds fake positionals metavar at the end of the usage line
        """
        if self._positionals_metavar is None:
            return usage

        returned = ""
        added_metavars = False
        for line in cStringIO(usage):
            if not added_metavars and not line.strip():
                returned = returned[:-1] + " [{0} [{0} ...]] \n".format(self._positionals_metavar)
            returned += line
        return returned

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

COLOR_RESET = colorama.Fore.RESET + colorama.Back.RESET + colorama.Style.RESET_ALL  # pylint: disable=no-member


def make_styler(style):
    return lambda s: '{0}{1}{2}'.format(style, s, COLOR_RESET)

UNDERLINED = '\x1b[4m'


def error_abort(message, *args):
    if args:
        message = message.format(*args)
    print(message, file=sys.stderr)
    sys.exit(-1)
