#!/usr/bin/env python
import argparse
import os
import sys

import random

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("dir")

class Application(object):

    _INDENT = " " * 4

    def __init__(self, args):
        self._args = args

    def generate_error_test(self):
        return "unused = nonexisting_variable"

    def generate_failing_test(self):
        return "assert self.f(1) <= self.f(0)"

    def generate_skipping_test(self):
        return "slash.skip_test('skipped')"

    def main(self):
        os.makedirs(self._args.dir)
        for i in range(3):
            filename = os.path.join(self._args.dir, "test_{0}.py".format(i))
            with open(filename, "w") as f:
                f.write("import slash\n")
                f.write("\n")
                f.write("class Test(slash.Test):\n")
                f.write(self._INDENT)
                f.write("def f(self, x):\n")
                f.write(self._INDENT * 2)
                f.write("return x\n")

                generators = [self.generate_error_test, self.generate_skipping_test, self.generate_failing_test]
                random.shuffle(generators)
                for index, generator in enumerate(generators):
                    f.write(self._INDENT)
                    f.write("def test_{0}(self):\n".format(index))
                    f.write(self._INDENT * 2)
                    f.write("self._test_{0}_step1()".format(index))
                    f.write("\n\n")
                    for step in range(1, 5):
                        f.write(self._INDENT)
                        f.write("def _test_{0}_step{1}(self):\n".format(index, step))
                        f.write(self._INDENT * 2)
                        f.write("func_step={0}\n".format(step))
                        f.write(self._INDENT * 2)
                        f.write("some_var={0}\n".format(random.randrange(10)))
                        f.write(self._INDENT * 2)
                        if step == 4:
                            f.write(generator())
                        else:
                            f.write("self._test_{0}_step{1}()\n".format(index, step+1))
                        f.write("\n\n")


        return 0


#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    app = Application(args)
    sys.exit(app.main())


if __name__ == "__main__":
    main_entry_point()
