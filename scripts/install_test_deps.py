#! /usr/bin/python

import subprocess
import sys
import os

_PYPY = hasattr(sys, "pypy_version_info")

_BIN_PATH = os.path.dirname(sys.executable)

if __name__ == '__main__':
    deps = [
        "coverage",
        "coveralls",
        "pytest",
        "pytest-capturelog",
        "pyforge",
        "lxml", # for XSD validations
    ]
    if not _PYPY:
        deps.append("pylint>=1.0.0")
    if sys.version_info < (2, 7):
        deps.append("unittest2")

    subprocess.check_call("{0} install --use-mirrors {1}".format(
        os.path.join(_BIN_PATH, "pip"),
        " ".join(repr(dep) for dep in deps)), shell=True)

