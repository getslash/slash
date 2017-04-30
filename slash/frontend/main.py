#!/usr/bin/env python
from __future__ import print_function
import argparse
import contextlib
import logbook # pylint: disable=F0401
import sys

from ..__version__ import __version__

_COMMANDS = {
    "run": "slash.frontend.slash_run:slash_run",
    "resume": "slash.frontend.slash_run:slash_resume",
    "version": "slash.frontend.main:slash_version",
    "list": "slash.frontend.slash_list:slash_list",
    "list-config": "slash.frontend.list_config:list_config",
    "list-plugins": "slash.frontend.slash_list_plugins:slash_list_plugins",
}


def _get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available commands:\n\t{0}".format("\n\t".join(sorted(_COMMANDS))),
        usage="%(prog)s command...",
    )

    parser.add_argument("-v", action="append_const", const=1, dest="verbosity", default=[],
                        help="Be more verbose. Can be specified multiple times to increase verbosity further")
    parser.add_argument("cmd")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    return parser

def main():
    parser = _get_parser()
    args = parser.parse_args()
    with _setup_logging_context(args):
        module_name = _COMMANDS.get(args.cmd)
        if not module_name:
            parser.error("No such command: {0}".format(args.cmd))
        module_name, func_name = module_name.split(":")
        module = __import__(module_name, fromlist=[""])
        func = getattr(module, func_name)
        returned = func(args.argv)
        if not isinstance(returned, int):
            returned = returned.exit_code
    return returned

def slash_version(_):
    print('Slash v{0}'.format(__version__))
    return 0

################################## Boilerplate ################################
_DEFAULT_LOG_LEVEL = logbook.WARNING
@contextlib.contextmanager
def _setup_logging_context(args):
    log_level = max(logbook.DEBUG, _DEFAULT_LOG_LEVEL - len(args.verbosity))
    with logbook.NullHandler().applicationbound():
        with logbook.StderrHandler(level=log_level, bubble=False).applicationbound():
            yield

#### For use with entry_points/console_scripts
def main_entry_point():
    sys.exit(main())

if __name__ == "__main__":
    main_entry_point()
