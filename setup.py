from setuptools import setup, find_packages
import functools
import os
import platform

_PYTHON_VERSION = platform.python_version()
_in_same_dir = functools.partial(os.path.join, os.path.dirname(__file__))

with open(_in_same_dir("slash", "__version__.py")) as version_file:
    exec(version_file.read())  # pylint: disable=W0122

install_requires = [
    "arrow",
    "colorama",
    "confetti>=2.4.1",
    "dessert",
    "emport>=1.0.0",
    "gossip>=1.0.0",
    "Logbook>=0.11.2",
    "requests>=1.1.0",
    "raven",
    "py>=1.4.20",
    "pyparsing",
    # DO NOT ADD pyforge, lxml or any other package only required for testing
]

if _PYTHON_VERSION < "2.7":
    install_requires.append("argparse")
    install_requires.append("ordereddict")

if _PYTHON_VERSION < "3.3":
    install_requires.append("contextlib2")

setup(name="slash",
      classifiers=[
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
      ],
      description="A Testing Framework",
      license="BSD",
      author="Rotem Yaari",
      author_email="vmalloc@gmail.com",
      url="http://vmalloc.github.io/slash",
      version=__version__,  # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),
      install_requires=install_requires,
      entry_points=dict(
          console_scripts=[
              "slash  = slash.frontend.main:main_entry_point",
          ]
      ),
)
