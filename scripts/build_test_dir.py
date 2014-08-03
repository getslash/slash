#!/usr/bin/env python
import argparse
import sys

import random

from tests.utils.suite import TestSuite

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument('--fixtures', dest='use_fixtures', action='store_true', default=False)
parser.add_argument("dir")
parser.add_argument("summary")

class Application(object):

    _INDENT = " " * 4

    def __init__(self, args):
        self._args = args

    def main(self):

        s = TestSuite(self._args.dir)
        if not self._args.summary:
            parser.error("No summary given")
        for index, element in enumerate(self._args.summary):
            t = s.add_test()
            if self._args.use_fixtures and index % 3 == 0:
                if index % 2 == 0:
                    f = t.add_fixture(t.file.add_fixture())
                else:
                    f = t.add_fixture(s.add_fixture())
                f.parametrize()

            if element == '.':
                pass
            elif element == 'F':
                t.fail()
            elif element == 'E':
                t.error()
            elif element == 'S':
                t.skip()
            else:
                parser.error("Unknown marker: {0!r}".format(element))

        s.commit()

        return 0


#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    app = Application(args)
    sys.exit(app.main())


if __name__ == "__main__":
    main_entry_point()
