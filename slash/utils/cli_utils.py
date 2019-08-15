from __future__ import print_function
import argparse
import os
import sys
from contextlib import contextmanager

import colorama

from .. import conf, plugins


_PLUGIN_ACTIVATION_PREFIX = "--with-"
_PLUGIN_DEACTIVATION_PREFIX = "--without-"

def add_pending_plugins_from_commandline(argv):
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

def configure_arg_parser_by_plugins(parser):
    for plugin in plugins.manager.get_installed_plugins().values():
        group = parser.add_argument_group('Options for {}{}'.format(
            '' if plugins.manager.is_internal_plugin(plugin) else '--with-',
            plugins.manager.normalize_command_line_name(plugin.get_name())))
        plugin.configure_argument_parser(group)

def configure_arg_parser_by_config(parser, config=None):
    if config is None:
        config = conf.config

    plugin_groups = {}

    parser.add_argument(
        "-o", dest="config_overrides", metavar="PATH=VALUE", action="append",
        default=[],
        help="Provide overrides for configuration"
    )
    for path, node, cmdline in _iter_cmdline_config(config):
        if path.startswith('plugin_config.'):
            plugin_name = path.split('.')[1]
            subparser = plugin_groups.get(plugin_name)
            if subparser is None:
                subparser = plugin_groups[plugin_name] = parser.add_argument_group(
                    'options for the {0} plugin (--with-{0})'.format(plugin_name))
        else:
            subparser = parser
        cmdline.configure_parser(subparser, path, node)

def configure_plugins_from_args(args):
    for plugin in plugins.manager.get_active_plugins().values():
        plugin.configure_from_parsed_args(args)

def _iter_cmdline_config(config):
    for path, cfg in config.traverse_leaves():
        cmdline = (cfg.metadata or {}).get("cmdline")
        if cmdline is None:
            continue
        yield path, cfg, cmdline

@contextmanager
def get_modified_configuration_from_args_context(parser, args, config=None):
    if config is None:
        config = conf.config
    to_restore = []
    try:
        for path, cfg, cmdline in _iter_cmdline_config(config):
            old_value = cfg.get_value()
            new_value = cmdline.update_value(old_value, args)
            if new_value != old_value:
                to_restore.append((path, cfg.get_value()))
                try:
                    config.assign_path(path, new_value, deduce_type=True, default_type=str)
                except ValueError:
                    parser.error('Invalid value for {}: {!r}'.format(cmdline, new_value))
        for override in args.config_overrides:
            if "=" not in override:
                parser.error("Invalid config override: {}".format(override))
            path, _ = override.split("=", 1)
            to_restore.append((path, config.get_path(path)))
            try:
                config.assign_path_expression(override, deduce_type=True, default_type=str)
            except ValueError:
                parser.error("Invalid value for config override: {}".format(override))
        yield
    finally:
        for path, prev_value in reversed(to_restore):
            config.assign_path(path, prev_value)

class SlashArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(SlashArgumentParser, self).__init__(
            prog=self._deduce_program_name(),
            usage='{} [options]'.format(self._deduce_program_name()),
            *args, **kwargs)

        self._positionals_metavar = None

    def _deduce_program_name(self):
        returned = os.path.basename(sys.argv[0])
        if len(sys.argv) > 1:
            returned += " {}".format(sys.argv[1])
        return returned

    def set_positional_metavar(self, metavar, plural=True):
        self._positionals_metavar = metavar
        if plural:
            self.usage += ' {0} [{0} [...]]'.format(metavar)
        else:
            self.usage += ' {}'.format(metavar)

    def set_description(self, description):
        self.description = description


COLOR_RESET = colorama.Fore.RESET + colorama.Back.RESET + colorama.Style.RESET_ALL  # pylint: disable=no-member


class ColorizedString(str):

    def __new__(cls, *args, **kwargs):
        style = kwargs.pop('style', None)
        returned = str.__new__(cls, *args, **kwargs)
        returned.style = style
        return returned

    def colorize(self):
        if self.style:
            return '{}{}{}'.format(self.style, self, COLOR_RESET)
        return str(self)

def make_styler(style):
    return lambda string: ColorizedString(string, style=style)

UNDERLINED = '\x1b[4m'

class Printer(object):

    def __init__(self, report_stread, enable_output=True, force_color=False, enable_color=True, error_stream=None):
        self._stream = report_stread
        self._error_stream = error_stream if error_stream is not None else self._stream
        self._output_enabled = enable_output
        self._force_color = force_color
        self._color_enabled = enable_color

    def _colored_print(self, *args, **print_kwargs):
        self._print(*(getattr(arg, 'colorize', arg.__str__)() for arg in args), **print_kwargs)

    def _print(self, *args, **print_kwargs):
        is_error = print_kwargs.pop('error', False)
        print_kwargs['file'] = self._error_stream if is_error else self._stream
        print(*args, **print_kwargs)

    def __call__(self, *args, **print_kwargs):
        if self._output_enabled:
            should_color = self._force_color or (self._color_enabled and self._stream.isatty())
            print_func = self._colored_print if should_color else self._print
            print_func(*args, **print_kwargs)


def error_abort(message, *args, **kwargs):
    stream = kwargs.pop('stream', sys.stderr)
    assert not kwargs
    if args:
        message = message.format(*args)
    print(message, file=stream)
    sys.exit(-1)
