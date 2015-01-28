from __future__ import print_function
from functools import partial
import inspect
import os
import colorama
import sys
import slash
from slash.utils.python import get_underlying_func


_COLOR_RESET = colorama.Fore.RESET + colorama.Back.RESET + colorama.Style.RESET_ALL # pylint: disable=no-member

def _title_style(s):
    # pylint: disable=no-member
    return '{0}{1}{2}{3}'.format(colorama.Fore.WHITE, colorama.Style.BRIGHT, s, _COLOR_RESET)


def _unused_style(s):
    # pylint: disable=no-member
    return '{0}{1}{2}'.format(colorama.Fore.YELLOW, s, _COLOR_RESET)



def _doc_style(s):
    # pylint: disable=no-member
    return '{0}{1}{2}{3}'.format(colorama.Fore.GREEN, colorama.Style.BRIGHT, s, _COLOR_RESET)


def slash_fixtures(args, report_stream=sys.stdout):
    _print = partial(print, file=report_stream)

    path = args[0] if args else '.'
    with slash.Session() as session:
        loader = slash.loader.Loader()
        runnables = loader.get_runnables([path])
        used_fixtures = set()
        for test in runnables:
            used_fixtures.update(test.get_needed_fixtures())

        for fixture in session.fixture_store:
            if not hasattr(fixture, 'fixture_func'):
                continue

            fixture_func = get_underlying_func(fixture.fixture_func)
            doc = inspect.cleandoc(fixture_func.__doc__) if fixture_func.__doc__ else ''

            unused_string = '' if fixture in used_fixtures else ' (Unused)'

            _print(_title_style('{0}{1}'.format(fixture.info.name, unused_string)))
            if doc:
                for line in (_doc_style(doc)).split('\n'):
                    _print('    {0}'.format(line))

            _print('    Source: {0}:{1}'.format(
                os.path.relpath(inspect.getsourcefile(fixture_func), path),
                inspect.getsourcelines(fixture_func)[1]))
            _print('\n')
