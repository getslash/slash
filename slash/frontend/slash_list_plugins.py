from __future__ import print_function

import argparse
import sys
from functools import partial

import colorama
from slash.utils.cli_utils import UNDERLINED, make_styler, error_abort

from slash.plugins import manager

_title_style = make_styler(colorama.Fore.WHITE + colorama.Style.BRIGHT)  # pylint: disable=no-member
_disabled_style = make_styler(colorama.Fore.BLACK + colorama.Style.BRIGHT)  # pylint: disable=no-member
_enabled_style = make_styler(colorama.Fore.GREEN)  # pylint: disable=no-member

_link_style = make_styler(colorama.Fore.CYAN)  # pylint: disable=no-member


def _get_parser():
    parser = argparse.ArgumentParser('slash list-plugins [options]')
    return parser


def slash_list_plugins(args, report_stream=sys.stdout):
    _print = partial(print, file=report_stream)

    parser = _get_parser()
    _ = parser.parse_args(args)

    active = manager.get_active_plugins()

    for plugin in sorted(manager.get_installed_plugins().values(), key=lambda p: p.get_name()):
        name = plugin.get_name()
        _print(_title_style(name), end=' ')
        if name in active:
            _print(_enabled_style('active (use --without-{} to deactivate'.format(name)))
        else:
            _print(_disabled_style('inactive (use --with-{} to activate)'.format(name)))
        if plugin.__doc__:
            _print('\t', plugin.__doc__.strip())
            _print('\t For more information see', _link_style('https://slash.readthedocs.org/en/master/builtin_plugins.html#{}'.format(name)))

    return 0
