#! /usr/bin/python
from __future__ import print_function
import subprocess
import sys
import os

_PYPY = hasattr(sys, "pypy_version_info")
_BIN_PATH = os.path.dirname(sys.executable)

def _cmd(cmd):
    cmd = "{0}/{1}".format(_BIN_PATH, cmd)
    print("+", cmd, file=sys.stderr)
    subprocess.check_call(cmd, shell=True)

if __name__ == '__main__':
    if not _PYPY:
        _cmd("pylint --rcfile=.pylintrc setup.py")
        _cmd("pylint --rcfile=.pylintrc slash")
    _cmd("coverage run {0}/nosetests -w tests".format(_BIN_PATH))
