from __future__ import print_function

import argparse
import sys
from functools import partial

import colorama
import slash
from slash.utils.cli_utils import make_styler

_config_name_style = make_styler(colorama.Fore.WHITE + colorama.Style.BRIGHT) # pylint: disable=no-member
_default_style = make_styler(colorama.Fore.GREEN + colorama.Style.BRIGHT) # pylint: disable=no-member
_INDENT = ' ' * 4

def _parse_args(args):
    parser = argparse.ArgumentParser('slash list-config [options] PATH...')
    return parser.parse_args(args)


def list_config(args, report_stream=sys.stdout):
    _print = partial(print, file=report_stream)

    args = _parse_args(args)

    with slash.Session():
        slash.site.load()

        for name, value in sorted(slash.config.traverse_leaves()):
            _print(_config_name_style(name), '--')
            _print(_INDENT, 'default:', _default_style(value.get_value()))
            if value.metadata and 'doc' in value.metadata:
                _print(_INDENT, value.metadata['doc'])
