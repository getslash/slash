from ..loader import Loader
from ..runner import run_tests
from ..session import Session
from ..suite import Suite
import argparse
import contextlib

def shake_run(args):
    args = _build_parser().parse_args(args)
    test_loader = Loader()
    with _suite_context() as suite:
        for path in args.paths:
            run_tests(test_loader.iter_runnable_tests(path))
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
