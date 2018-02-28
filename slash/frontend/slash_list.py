from __future__ import print_function

import argparse
import inspect
import itertools
import os
import sys
from functools import partial

import colorama
import slash
import slash.site
import slash.loader
from slash import config
from slash.exceptions import CannotLoadTests
from slash.utils.cli_utils import UNDERLINED, make_styler, Printer
from slash.utils.python import get_underlying_func
from slash.utils.suite_files import iter_suite_file_paths

_heading_style = make_styler(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + UNDERLINED)  # pylint: disable=no-member
_title_style = make_styler(colorama.Fore.WHITE + colorama.Style.BRIGHT)  # pylint: disable=no-member
_unused_style = make_styler(colorama.Fore.YELLOW)  # pylint: disable=no-member
_doc_style = make_styler(colorama.Fore.GREEN + colorama.Style.BRIGHT)  # pylint: disable=no-member
_override_style = make_styler(colorama.Fore.YELLOW + colorama.Style.BRIGHT)  # pylint: disable=no-member


def _get_parser():
    parser = argparse.ArgumentParser('slash list [options] PATH...')
    parser.add_argument('-f', '--suite-file', dest='suite_files', action='append', default=[])
    parser.add_argument('--only-fixtures', dest='only', action='store_const', const='fixtures', default=None)
    parser.add_argument('--only-tests', dest='only', action='store_const', const='tests', default=None)
    parser.add_argument('--show-tags', dest='show_tags', action='store_true', default=False)
    parser.add_argument('--no-params', dest='show_params', action='store_false', default=True)
    parser.add_argument('--allow-empty', dest='allow_empty', action='store_true', default=False)
    parser.add_argument('--warnings-as-errors', dest='warnings_as_errors', action='store_true', default=False)
    parser.add_argument('-r', '--relative-paths', action='store_true', default=False)
    parser.add_argument('--no-output', dest='show_output', action='store_false', default=True)
    parser.add_argument('--force-color', dest='force_color', action='store_true', default=False)
    parser.add_argument('--no-color', dest='enable_color', action='store_false', default=True)

    parser.add_argument('paths', nargs='*', default=[], metavar='PATH')
    return parser


def slash_list(args, report_stream=sys.stdout, error_stream=sys.stderr):
    _print = partial(print, file=report_stream)

    parser = _get_parser()
    parsed_args = parser.parse_args(args)

    _print = Printer(report_stream, enable_output=parsed_args.show_output, force_color=parsed_args.force_color,
                     enable_color=parsed_args.enable_color)
    try:
        with slash.Session() as session:
            slash.site.load()

            if not parsed_args.paths and not parsed_args.suite_files:
                parsed_args.paths = config.root.run.default_sources

            if not parsed_args.paths and not parsed_args.suite_files:
                parser.error('Neither test paths nor suite files were specified')

            loader = slash.loader.Loader()
            runnables = loader.get_runnables(itertools.chain(parsed_args.paths, iter_suite_file_paths(parsed_args.suite_files)))
            used_fixtures = set()
            for test in runnables:
                used_fixtures.update(test.get_required_fixture_objects())

            if parsed_args.only in (None, 'fixtures'):
                _report_fixtures(parsed_args, session, _print, used_fixtures)

            if parsed_args.only in (None, 'tests'):
                _report_tests(parsed_args, runnables, _print)

        if bool(session.warnings.warnings) and parsed_args.warnings_as_errors:
            return -1
        if len(runnables):  # pylint: disable=len-as-condition
            return 0
    except CannotLoadTests as e:
        print('Could not load tests ({})'.format(e), file=error_stream)
        return -1
    print('No tests were found!', file=sys.stderr)
    return int(not parsed_args.allow_empty)


def _report_tests(args, runnables, printer):
    if not args.only:
        printer(_heading_style('Tests'))

    visited = set()

    for runnable in runnables:
        extra = "" if not args.show_tags else "  Tags: {0}".format(list(runnable.get_tags()))
        address = runnable.__slash__.address
        if not args.show_params:
            address = address.split('(')[0]
        if args.relative_paths:
            address = _convert_address_to_relpath(address)
        if address in visited:
            continue
        visited.add(address)
        printer("{0}{1}".format(_title_style(address), extra))


def _convert_address_to_relpath(address):
    filename, remainder = address.split(':', 1)
    if os.path.isabs(filename):
        filename = os.path.relpath(filename)
    return '{}:{}'.format(filename, remainder)


def _report_fixtures(args, session, printer, used_fixtures):
    if not args.only:
        printer(_heading_style('Fixtures'))
    for fixture in session.fixture_store:
        if not hasattr(fixture, 'fixture_func'):
            continue

        fixture_func = get_underlying_func(fixture.fixture_func)
        doc = inspect.cleandoc(fixture_func.__doc__) if fixture_func.__doc__ else ''

        if fixture.info.autouse:
            additional_info = ' (Autouse)'
        elif fixture not in used_fixtures:
            additional_info = ' (Unused)'
        else:
            additional_info = ''

        if fixture.is_override():
            additional_info += ' -- ' + _override_style('Override')

        printer(_title_style('{0}{1}'.format(fixture.info.name, additional_info)))
        if doc:
            for line in (_doc_style(doc)).split('\n'):
                printer('    {0}'.format(line))

        printer('    Source: {0}:{1}'.format(
            os.path.relpath(inspect.getsourcefile(fixture_func), args.paths[0] if args.paths else '.'),
            inspect.getsourcelines(fixture_func)[1]))
        printer('\n')
