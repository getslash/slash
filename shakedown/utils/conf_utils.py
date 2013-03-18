from confetti import Metadata
from confetti.utils import assign_path, get_path, assign_path_expression
from contextlib import contextmanager
import argparse
import itertools
from six import iteritems

def Doc(msg):
    return Metadata(doc=msg)

_dest_generator = ("dest_{0}".format(i) for i in itertools.count())

class _Cmdline(object):
    def __init__(self, arg=None, on=None, off=None):
        super(_Cmdline, self).__init__()
        self.arg = arg
        self.on = on
        self.off = off
    def populate_parser_options(self, path, assignment_map, parser):
        dest = next(_dest_generator)
        if self.arg:
            parser.add_argument(self.arg, dest=dest)
        if self.on:
            parser.add_argument(self.on, action="store_true", dest=dest, default=None)
        if self.off:
            parser.add_argument(self.off, action="store_false", dest=dest, default=None)
        assignment_map[dest] = path

def Cmdline(**kwargs):
    return Metadata(cmdline=_Cmdline(**kwargs))

@contextmanager
def get_parsed_config_args_context(config, args):
    """
    Attempts to parse all config-related parameters from command line. The inner context
    receives the remainder of the argument list after parsing
    """
    assignment_map, parsed_args, args = _parse_args(config, args)
    backups = _assign_paths(config, assignment_map, parsed_args)
    try:
        yield args
    finally:
        _restore_backups(config, backups)

def _parse_args(config, args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", dest="config_overrides", metavar="PATH=VALUE", action="append",
        default=[],
        help="Provide overrides for configuration"
    )
    assignment_map = {}
    for path, cfg in config.traverse_leaves():
        cmdline = (cfg.metadata or {}).get("cmdline")
        if cmdline is None:
            continue
        cmdline.populate_parser_options(path, assignment_map, parser)
    parsed_args, remainder = parser.parse_known_args(args)
    return assignment_map, parsed_args, remainder

def _assign_paths(config, assignment_map, parsed_args):
    backups = []
    try:
        for dest, path in iteritems(assignment_map):
            value = getattr(parsed_args, dest, None)
            if value is None:
                continue
            backups.append((path, get_path(config, path)))
            assign_path(config, path, value)
        for override_string in parsed_args.config_overrides:
            path, _ = override_string.split("=", 1)
            backups.append((path, get_path(config, path)))
            assign_path_expression(config, override_string, deduce_type=True)
    except:
        _restore_backups(config, backups)
        raise
    return backups

def _restore_backups(config, backups):
    for path, value in backups:
        assign_path(config, path, value)
