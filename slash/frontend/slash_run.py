from ..app import get_application_context
from ..conf import config
from ..exceptions import SlashException
from ..runner import run_tests
from ..utils import cli_utils
from ..utils import rerunning_utils
import functools
import logbook
import sys

_logger = logbook.Logger(__name__)


def slash_run(args, report_stream=sys.stderr, rerun=False):
    with get_application_context(
            argv=args, args=_get_extra_cli_args() if not rerun else [],
            enable_interactive=True,
            report_stream=report_stream) as app:
        if rerun:
            try:
                app.prev_session_state = rerunning_utils.get_last_session_state()
            except IOError as e:
                logbook.error("Cannot load state file! ({0})", e)
                return -1
        else:
            app.prev_session_state = None

        iterator = _get_test_iterator(app, args)
        try:
            run_tests(iterator)
        except SlashException as e:
            logbook.error(e)
            return -1
        finally:
            _save_rerun_state(app)

        if app.session.result.is_success(allow_skips=True):
            return 0
        return -1

slash_rerun = functools.partial(slash_run, rerun=True)

def _get_test_iterator(app, args): # pylint: disable=unused-argument
    if app.prev_session_state:
        return _get_rerun_test_iterator(app)

    paths = app.args.paths
    if not paths:
        paths = config.root.run.default_sources
    if not paths and not app.args.interactive:
        app.error("No tests specified")

    return app.test_loader.iter_pqns(paths)

def _get_rerun_test_iterator(app):
    saved_results = app.prev_session_state["results"]

    for test in app.test_loader.iter_pqns(app.prev_session_state["pqns"]):
        _logger.debug("Rerun: examining {0}", test)

        saved_result = saved_results.get(test.__slash__.fqn.fqn, None)
        if saved_result is not None and not saved_result["rerun_needed"]:
            _logger.debug("Skipping {0} (no need to rerun)", test)
            continue
        _logger.debug("Rerun: retrying {0}", test)
        yield test

def _save_rerun_state(app):
    if app.prev_session_state is not None:
        state = app.prev_session_state
    else:
        state = {"pqns": app.args.paths, "results": {}}
    saved_results = state["results"]

    for result in app.session.result.iter_test_results():
        saved_result = saved_results.get(result.test_metadata.fqn.fqn, None)
        if saved_result is None:
            saved_result = saved_results[result.test_metadata.fqn.fqn] = {"rerun_needed": False}
        saved_result["rerun_needed"] = result.is_error() or result.is_failure()

    rerunning_utils.save_session_state(state)

def _get_extra_cli_args():
    return [
        cli_utils.Argument(
            "paths", metavar="TEST", nargs="*",
            help="Test name to run. This can be either a file or a test FQN. "
            "See documentation for details"),
        ]
