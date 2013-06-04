from ..app import get_application_context
from ..runner import run_tests
from ..utils import cli_utils
from ..utils.interactive import start_interactive_shell
import logbook
import sys

_logger = logbook.Logger(__name__)

def slash_run(args, report_stream=sys.stderr):
    with get_application_context(
            argv=args, args=_get_extra_cli_args(),
            report_stream=report_stream) as app:
        if not app.args.paths and not app.args.interactive:
            app.error("No tests specified")
        if app.args.interactive:
            start_interactive_shell()
        for path in app.args.paths:
            run_tests(app.test_loader.iter_path(path))
        if app.session.result.is_success():
            return 0
        return -1

def _get_extra_cli_args():
    return [
        cli_utils.Argument(
            "paths", metavar="TEST", nargs="*",
            help="Test name to run. This can be either a file or a test FQDN. "
            "See documentation for details"),
        cli_utils.Argument("-i", "--interactive", help="Enter an interactive shell before running tests",
                          action="store_true", default=False),
        ]
