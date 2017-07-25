import argparse
import sys

import colorama
from slash.utils.cli_utils import make_styler, Printer

from slash import site
from slash.plugins import manager

_title_style = make_styler(colorama.Fore.WHITE + colorama.Style.BRIGHT)  # pylint: disable=no-member
_disabled_style = make_styler(colorama.Fore.BLACK + colorama.Style.BRIGHT)  # pylint: disable=no-member
_enabled_style = make_styler(colorama.Fore.GREEN)  # pylint: disable=no-member

_link_style = make_styler(colorama.Fore.CYAN)  # pylint: disable=no-member


def _get_parser():
    parser = argparse.ArgumentParser('slash list-plugins [options]')
    parser.add_argument('--force-color', dest='force_color', action='store_true', default=False)
    parser.add_argument('--no-color', dest='enable_color', action='store_false', default=True)
    return parser


def slash_list_plugins(args, report_stream=sys.stdout):
    parser = _get_parser()
    parsed_args = parser.parse_args(args)

    _print = Printer(report_stream, force_color=parsed_args.force_color, enable_color=parsed_args.enable_color)

    site.load()

    active = manager.get_future_active_plugins()

    for plugin in sorted(manager.get_installed_plugins(include_internals=False).values(), key=lambda p: p.get_name()):
        name = plugin.get_name()
        _print(_title_style(name), end=' ')
        if name in active:
            _print(_enabled_style('active (use --without-{} to deactivate'.format(name)))
        else:
            _print(_disabled_style('inactive (use --with-{} to activate)'.format(name)))
        if plugin.__doc__:
            for line in plugin.__doc__.splitlines():
                if line.strip():
                    _print('\t', line.strip())

    return 0
