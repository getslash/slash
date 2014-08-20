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
    try:
        _cmd("py.test tests --cov=slash --cov-report=html")
        if not _PYPY:
            _cmd("pylint --rcfile=.pylintrc setup.py")
            _cmd("pylint --rcfile=.pylintrc slash")
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
