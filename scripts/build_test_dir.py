#!/usr/bin/env python
import argparse
import sys

import random

from tests.utils.suite_writer import Suite

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument('--fixtures', dest='use_fixtures', action='store_true', default=False)
parser.add_argument('--parameters', dest='use_parameters', action='store_true', default=False)
parser.add_argument('--debug-info', dest='debug_info', action='store_true', default=False)
parser.add_argument("dir")
parser.add_argument("summary")

_FIXTURE_FREQ = 3
_PARAM_FREQ = 4

class Application(object):

    _INDENT = " " * 4

    def __init__(self, args):
        self._args = args

    def main(self):

        s = Suite(path=self._args.dir, debug_info=self._args.debug_info)
        if not self._args.summary:
            parser.error("No summary given")
        for index, element in enumerate(self._args.summary):
            t = s.add_test()
            if self._args.use_fixtures and index % _FIXTURE_FREQ == 0:
                if index % 2 == 0:
                    t.depend_on_fixture(t.file.add_fixture())
                else:
                    t.depend_on_fixture(s.slashconf.add_fixture())

            if self._args.use_parameters and index % _PARAM_FREQ == 0:
                t.parametrize()

            if element == '.':
                pass
            elif element == 'F':
                t.when_run.fail()
            elif element == 'E':
                t.when_run.error()
            elif element == 'S':
                t.when_run.skip()
            elif element == 'i':
                t.when_run.interrupt()
            else:
                parser.error("Unknown marker: {!r}".format(element))

        s.commit()

        return 0


#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    app = Application(args)
    sys.exit(app.main())


if __name__ == "__main__":
    main_entry_point()
