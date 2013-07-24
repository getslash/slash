#! /usr/bin/python
from __future__ import print_function
import subprocess
import sys
import os

def _execute(cmd):
    if 0 != subprocess.call(cmd, shell=True):
        sys.exit(-1)

if __name__ == '__main__':
    print("Running from", os.path.abspath("."))
    deps = [
        "nose",
        "pyforge",
        "pylint",
    ]
    if sys.version_info < (2, 7):
        deps.append("unittest2")

    _execute("pip install --use-mirrors {0}".format(" ".join(deps)))

    _execute("python setup.py develop")

    if sys.version_info < (3, 3):
        _execute("pylint --rcfile=.pylintrc setup.py")
        _execute("pylint --rcfile=.pylintrc slash")
    _execute("nosetests -w tests")
