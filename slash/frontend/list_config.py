import argparse
import sys

import colorama
import slash
import slash.site
from slash.utils.cli_utils import make_styler, Printer

_config_name_style = make_styler(colorama.Fore.WHITE + colorama.Style.BRIGHT) # pylint: disable=no-member
_default_style = make_styler(colorama.Fore.GREEN + colorama.Style.BRIGHT) # pylint: disable=no-member
_INDENT = ' ' * 4

def _parse_args(args):
    parser = argparse.ArgumentParser(prog='slash list-config')
    parser.add_argument('paths', nargs='*', default=[])
    parser.add_argument('--force-color', dest='force_color', action='store_true', default=False)
    parser.add_argument('--no-color', dest='enable_color', action='store_false', default=True)
    return parser.parse_args(args)


def list_config(args, report_stream=sys.stdout):

    args = _parse_args(args)
    _print = Printer(report_stream, force_color=args.force_color, enable_color=args.enable_color)

    filters = _parse_filters(args.paths)

    slash.site.load()
    with slash.Session():

        for name, value in sorted(slash.config.traverse_leaves()):
            if not _is_included(name, filters):
                continue
            _print(_config_name_style(name), '--')
            _print(_INDENT, 'default:', _default_style(value.get_value()))
            if value.metadata and 'doc' in value.metadata:
                _print(_INDENT, value.metadata['doc'])
    return 0


def _parse_filters(paths):
    returned = set()
    for p in paths:
        returned.update(_iter_subpaths(p))
    return returned

def _iter_subpaths(p):
    p = p.split('.')
    for i in range(len(p)):
        yield '.'.join(p[:i+1])


def _is_included(name, filters):
    if not filters:
        return True
    for subpath in _iter_subpaths(name):
        if subpath in filters:
            return True
    return False
