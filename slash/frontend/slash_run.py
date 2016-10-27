import itertools
import functools
import sys
from contextlib import contextmanager

import logbook

from ..app import get_application_context
from ..conf import config
from ..exceptions import SlashException
from ..exception_handling import handling_exceptions
from ..resuming import (get_last_resumeable_session_id, get_tests_to_resume,
                        save_resume_state)
from ..runner import run_tests
from ..utils.interactive import generate_interactive_test
from ..utils.suite_files import iter_suite_file_paths

_logger = logbook.Logger(__name__)

def slash_run(args, report_stream=None, resume=False, app_callback=None):
    if report_stream is None:
        report_stream = sys.stderr
    with _get_slash_app_context(args, report_stream, resume) as app:
        if app_callback is not None:
            app_callback(app)
        try:
            with handling_exceptions():
                if resume:
                    session_ids = app.args.positionals
                    if not session_ids:
                        session_ids = [get_last_resumeable_session_id()]
                    to_resume = [x for session_id in session_ids for x in get_tests_to_resume(session_id)]
                    collected = app.test_loader.get_runnables(to_resume)
                else:
                    collected = _collect_tests(app, args)
                if app.args.interactive:
                    collected = itertools.chain([generate_interactive_test()], collected)
            with app.session.get_started_context():
                run_tests(collected)

        except SlashException as e:
            app.session.reporter.report_error_message(str(e))
            return -1
        finally:
            save_resume_state(app.session.results)

        if app.session.results.is_success(allow_skips=True):
            return 0
        return -1

@contextmanager
def _get_slash_app_context(args, report_stream, resume_session):
    with get_application_context(
            argv=args, positionals_metavar="SESSION_ID" if resume_session else "TEST",
            enable_interactive=True,
            report_stream=report_stream) as app:
        yield app

slash_resume = functools.partial(slash_run, resume=True)

def _collect_tests(app, args):  # pylint: disable=unused-argument
    paths = app.args.positionals

    paths = _extend_paths_from_suite_files(paths)

    if not paths and not app.args.interactive:
        paths = config.root.run.default_sources


    if not paths and not app.args.interactive:
        app.error("No tests specified")

    collected = app.test_loader.get_runnables(paths)
    if len(collected) == 0 and not app.args.interactive:
        app.error("No tests could be collected", usage=False)

    return collected

def _extend_paths_from_suite_files(paths):
    suite_files = config.root.run.suite_files
    if not suite_files:
        return paths
    paths = list(paths)
    paths.extend(iter_suite_file_paths(suite_files))
    return paths

