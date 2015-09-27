from __future__ import print_function

import argparse
import inspect
import os
import sys
from functools import partial

import colorama
import slash
from slash.utils.cli_utils import make_styler, UNDERLINED
from slash.utils.python import get_underlying_func


_heading_style = make_styler(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + UNDERLINED)  # pylint: disable=no-member
_title_style = make_styler(colorama.Fore.WHITE + colorama.Style.BRIGHT)  # pylint: disable=no-member
_unused_style = make_styler(colorama.Fore.YELLOW)  # pylint: disable=no-member
_doc_style = make_styler(colorama.Fore.GREEN + colorama.Style.BRIGHT)  # pylint: disable=no-member


def _parse_args(args):
    parser = argparse.ArgumentParser('slash list [options] PATH...')
    parser.add_argument('--only-fixtures', dest='only', action='store_const', const='fixtures', default=None)
    parser.add_argument('--only-tests', dest='only', action='store_const', const='tests', default=None)
    parser.add_argument('paths', nargs='+', default=['.'])
    return parser.parse_args(args)


def slash_list(args, report_stream=sys.stdout):
    _print = partial(print, file=report_stream)

    args = _parse_args(args)

    with slash.Session() as session:
        slash.site.load()
        loader = slash.loader.Loader()
        runnables = loader.get_runnables(args.paths)
        used_fixtures = set()
        for test in runnables:
            used_fixtures.update(test.get_required_fixture_objects())

        if args.only in (None, 'fixtures'):
            _report_fixtures(args, session, _print, used_fixtures)

        if args.only in (None, 'tests'):
            _report_tests(args, runnables, _print)


def _report_tests(args, runnables, printer):
    if not args.only:
        printer(_heading_style('Tests'))
    for runnable in runnables:
        printer(_title_style(runnable.__slash__.address))


def _report_fixtures(args, session, printer, used_fixtures):
    if not args.only:
        printer(_heading_style('Fixtures'))
    for fixture in session.fixture_store:
        if not hasattr(fixture, 'fixture_func'):
            continue

        fixture_func = get_underlying_func(fixture.fixture_func)
        doc = inspect.cleandoc(fixture_func.__doc__) if fixture_func.__doc__ else ''

        unused_string = '' if fixture in used_fixtures else ' (Unused)'

        printer(_title_style('{0}{1}'.format(fixture.info.name, unused_string)))
        if doc:
            for line in (_doc_style(doc)).split('\n'):
                printer('    {0}'.format(line))

        printer('    Source: {0}:{1}'.format(
            os.path.relpath(inspect.getsourcefile(fixture_func), args.paths[0]),
            inspect.getsourcelines(fixture_func)[1]))
        printer('\n')
