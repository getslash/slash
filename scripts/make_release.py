#!/usr/bin/env python
import argparse
import logging
import os
import sys
import subprocess
import time

def _from_root(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", *p))

_VERSION_FILE = _from_root("slash", "__version__.py")
_CHANGELOG_FILE = _from_root("doc", "changelog.rst")

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("-v", action="append_const", const=1, dest="verbosity", default=[],
                    help="Be more verbose. Can be specified multiple times to increase verbosity further")


def main(args):
    default = _get_default_next_version()
    version = raw_input("New version to release (default: {!r}): ".format(default)).strip()
    if not version:
        version = default
    subprocess.check_call('git flow release start {}'.format(version), shell=True)
    _write_new_version(version)
    _write_changelog(version)
    subprocess.check_call("git commit -a -m 'v{}'".format(version), shell=True)
    subprocess.check_call('git flow release finish {}'.format(version), shell=True)
    return 0

def _get_default_next_version():
    major, minor, bugfix = _get_current_version()
    return "{}.{}.{}".format(major, minor, bugfix + 1)

def _get_current_version():
    d = {}
    with open(_VERSION_FILE) as version_file:
        exec(version_file.read(), d, d)

    return [int(x) for x in d["__version__"].split(".")]

def _write_new_version(version):
    with open(_VERSION_FILE, "w") as version_file:
        version_file.write("__version__ = {!r}\n".format(version))

def _write_changelog(version):
    temp_filename = "/tmp/__bump_version_changelog.rst"
    with open(_CHANGELOG_FILE) as changelog_file:
        with open(temp_filename, "w") as temp_file:
            already_wrote = False
            for line in changelog_file:
                if line.startswith("* ") and not already_wrote:
                    temp_file.write("* :release:`{} <{}>`\n".format(
                        version,
                        time.strftime("%d-%m-%Y"),
                        ))
                    already_wrote = True
                temp_file.write(line)
    os.rename(temp_filename, _CHANGELOG_FILE)

#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    sys.exit(main(args))


if __name__ == "__main__":
    main_entry_point()
