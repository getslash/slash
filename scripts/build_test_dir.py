#!/usr/bin/env python
import argparse
import sys

import random

from tests.utils.suite import TestSuite

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("dir")

class Application(object):

    _INDENT = " " * 4

    def __init__(self, args):
        self._args = args

    def main(self):

        s = TestSuite(self._args.dir)
        for i in range(10):
            s.add_test()

        s.commit()

        return 0


#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    app = Application(args)
    sys.exit(app.main())


if __name__ == "__main__":
    main_entry_point()
