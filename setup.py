import os
import functools
from setuptools import setup, find_packages

_in_same_dir = functools.partial(os.path.join, os.path.dirname(__file__))

with open(_in_same_dir("shakedown", "__version__.py")) as version_file:
    exec(version_file.read())  # pylint: disable=W0122

install_requires = [
    "six",
]

setup(name="shakedown",
      classifiers = [
          "Programming Language :: Python :: 2.7",
          ],
      description="",
      license="BSD",
      author="Rotem Yaari",
      author_email="vmalloc@gmail.com",
      version=__version__, # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),
      install_requires=install_requires,
      scripts=[],
      )
