from ..conf import config
from ..loader import Loader
from ..runner import run_tests
from ..session import Session
from ..suite import Suite
from ..utils.conf_utils import get_parsed_config_args_context
from ..utils.reporter import Reporter
import argparse
import contextlib
import logbook
import sys

_logger = logbook.Logger(__name__)

def shake_run(args, report_stream=sys.stderr):
    with get_parsed_config_args_context(config, args) as args:
        args = _build_parser().parse_args(args)
        test_loader = Loader()
        with _suite_context() as suite:
            for path in args.paths:
                run_tests(test_loader.iter_runnable_tests(path))
        Reporter(report_stream).report_suite(suite)
        if suite.result.is_success():
            return 0
        return -1

def _build_parser():
    returned = argparse.ArgumentParser("shake run")
    returned.add_argument("paths", metavar="TEST", nargs="+",
                          help="Test name to run. This can be either a file or a test FQDN. "
                          "See documentation for details")
    return returned

@contextlib.contextmanager
def _suite_context():
    with Session():
        with Suite() as suite:
            yield suite
