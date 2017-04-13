#! /usr/bin/python

import subprocess
import sys
import os

_BIN_PATH = os.path.dirname(sys.executable)

if __name__ == '__main__':
    deps = [
        "coverage",
        "coveralls",
        "munch",
        "pytest",
        "pytest-xdist",
        "pytest-capturelog",
        "pytest-cov",
        "pytest-timeout",
        "pyforge",
        "pylint~=1.6.0",
    ]

    subprocess.check_call("{0} install {1}".format(
        os.path.join(_BIN_PATH, "pip"),
        " ".join(repr(dep) for dep in deps)), shell=True)
