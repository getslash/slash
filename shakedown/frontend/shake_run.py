from .. import hooks as trigger_hook
from .. import site
from ..loader import Loader
from ..runner import run_tests
from ..session import Session
from ..utils import cli_utils
from ..utils.interactive import start_interactive_shell
from ..utils.reporter import report_context
import logbook
import sys

_logger = logbook.Logger(__name__)

def shake_run(args, report_stream=sys.stderr):
    site.load()
    parser = _build_parser()
    with cli_utils.get_cli_environment_context(argv=args, parser=parser) as args:
        test_loader = Loader()
        with Session() as session:
            with report_context(report_stream):
                if not args.paths and not args.interactive:
                    parser.error("No tests specified")
                if args.interactive:
                    start_interactive_shell()
                for path in args.paths:
                    run_tests(test_loader.iter_runnable_tests(path))
            trigger_hook.result_summary()
        if session.result.is_success():
            return 0
        return -1

def _build_parser():
    returned = cli_utils.PluginAwareArgumentParser("shake run")
    returned.add_argument("-i", "--interactive", help="Enter an interactive shell before running tests",
                          action="store_true", default=False)
    returned.add_argument("paths", metavar="TEST", nargs="*",
                          help="Test name to run. This can be either a file or a test FQDN. "
                          "See documentation for details")
    return returned
