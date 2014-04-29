import functools
import sys
from contextlib import contextmanager

import logbook

from ..app import get_application_context
from ..conf import config
from ..exceptions import SlashException
from ..resuming import (get_last_resumeable_session_id, get_tests_to_resume,
                        save_resume_state)
from ..runner import run_tests

_logger = logbook.Logger(__name__)

def slash_run(args, report_stream=None, resume=False):
    if report_stream is None:
        report_stream = sys.stderr
    with _get_slash_app_context(args, report_stream, resume) as app:
        try:
            if resume:
                session_ids = app.args.positionals
                if not session_ids:
                    session_ids = [get_last_resumeable_session_id()]
                to_resume = [x for session_id in session_ids for x in get_tests_to_resume(session_id)]
                collected = app.test_loader.get_runnables(to_resume)
            else:
                collected = _collect_tests(app, args)
            run_tests(collected)
        except SlashException as e:
            logbook.error(str(e))
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
    if not paths and not app.args.interactive:
        paths = config.root.run.default_sources

    paths = _extend_paths_from_suite_files(paths)

    if not paths and not app.args.interactive:
        app.error("No tests specified")

    return app.test_loader.get_runnables(paths)

def _extend_paths_from_suite_files(paths):
    suite_files = config.root.run.suite_files
    if not suite_files:
        return paths
    paths = list(paths)
    for filename in suite_files:
        for line in open(filename):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            paths.append(line)
    return paths
