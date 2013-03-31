from setuptools import setup, find_packages
import functools
import os
import platform

_PYTHON_VERSION = platform.python_version()
_in_same_dir = functools.partial(os.path.join, os.path.dirname(__file__))

with open(_in_same_dir("shakedown", "__version__.py")) as version_file:
    exec(version_file.read())  # pylint: disable=W0122

install_requires = [
    "confetti>=2.0.0.dev0",
    "six",
]

if _PYTHON_VERSION < "3.0":
    install_requires.append("logbook")
    install_requires.append("raven")
else:
    # logbook 0.4.1 is broken under python 3
    install_requires.append("logbook==0.4.0")

if _PYTHON_VERSION < "2.7":
    install_requires.append("argparse")

setup(name="shakedown",
      classifiers = [
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.2",
          "Programming Language :: Python :: 3.3",
          ],
      description="A Testing Framework",
      license="BSD",
      author="Rotem Yaari",
      author_email="vmalloc@gmail.com",
      version=__version__, # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),
      install_requires=install_requires,
      entry_points = dict(
          console_scripts = [
              "shake  = shakedown.frontend.main:main_entry_point",
              ]
          ),

      )
