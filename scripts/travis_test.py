#! /usr/bin/python

import subprocess
import sys
import os

_PYPY = hasattr(sys, "pypy_version_info")

if __name__ == '__main__':
    if not _PYPY:
        subprocess.check_call("pylint --rcfile=.pylintrc setup.py", shell=True)
        subprocess.check_call("pylint --rcfile=.pylintrc slash", shell=True)
    subprocess.check_call("coverage run $(which nosetests) -w tests", shell=True)
