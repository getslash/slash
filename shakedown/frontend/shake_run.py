from .. import hooks as trigger_hook
from ..loader import Loader
from ..runner import run_tests
from ..session import Session
from ..suite import Suite
from ..utils import cli_utils
from ..utils.reporter import Reporter
import contextlib
import logbook
import sys

_logger = logbook.Logger(__name__)

def shake_run(args, report_stream=sys.stderr):
    parser = _build_parser()
    with cli_utils.get_cli_environment_context(argv=args, parser=parser) as args:
        test_loader = Loader()
        with _suite_context() as suite:
            for path in args.paths:
                run_tests(test_loader.iter_runnable_tests(path))
            trigger_hook.result_summary()
        Reporter(report_stream).report_suite(suite)
        if suite.result.is_success():
            return 0
        return -1

def _build_parser():
    returned = cli_utils.PluginAwareArgumentParser("shake run")
    returned.add_argument("paths", metavar="TEST", nargs="+",
                          help="Test name to run. This can be either a file or a test FQDN. "
                          "See documentation for details")
    return returned

@contextlib.contextmanager
def _suite_context():
    with Session():
        with Suite() as suite:
            yield suite
