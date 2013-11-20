#! /usr/bin/python

import subprocess
import sys
import os

_PYPY = hasattr(sys, "pypy_version_info")
_BIN_PATH = os.path.dirname(sys.executable)

def _cmd(cmd):
    subprocess.check_call("{0}/{1}".format(_BIN_PATH, cmd), shell=True)

if __name__ == '__main__':
    if not _PYPY:
        _cmd("pylint --rcfile=.pylintrc setup.py")
        _cmd("pylint --rcfile=.pylintrc slash")
    _cmd("coverage run $(which nosetests) -w tests")
