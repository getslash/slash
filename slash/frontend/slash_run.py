from ..app import get_application_context
from ..exceptions import SlashException
from ..runner import run_tests
from ..utils import cli_utils
import logbook
import os
import sys

_logger = logbook.Logger(__name__)

def slash_run(args, report_stream=sys.stderr):
    with get_application_context(
            argv=args, args=_get_extra_cli_args(),
            enable_interactive=True,
            report_stream=report_stream) as app:
        if not app.args.paths and not app.args.interactive:
            app.error("No tests specified")
        try:
            run_tests(app.test_loader.iter_paths(app.args.paths))
        except SlashException as e:
            logbook.error(e)
            return -1
        if app.session.result.is_success():
            return 0
        return -1

def _get_extra_cli_args():
    return [
        cli_utils.Argument(
            "paths", metavar="TEST", nargs="*",
            help="Test name to run. This can be either a file or a test FQDN. "
            "See documentation for details"),
        ]
