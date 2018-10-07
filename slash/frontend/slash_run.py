import functools
import sys
import logbook
from ..app import Application
from ..conf import config
from ..exception_handling import handling_exceptions
from ..exceptions import CannotLoadTests, InteractiveParallelNotAllowed
from ..resuming import (get_last_resumeable_session_id, get_tests_from_previous_session, save_resume_state, clean_old_entries)
from ..runner import run_tests
from ..utils.suite_files import iter_suite_file_paths
from ..utils.tmux_utils import run_slash_in_tmux
from ..plugins import manager
from ..parallel.parallel_manager import ParallelManager
from ..parallel.worker import Worker

_logger = logbook.Logger(__name__)

def slash_run(args, report_stream=None, resume=False, rerun=False, app_callback=None, working_directory=None):
    if report_stream is None:
        report_stream = sys.stderr
    app = Application()
    if resume:
        app.arg_parser.set_positional_metavar('SESSION-ID', plural=False)
        app.arg_parser.set_description('Resumes a previously run session by running only unsuccessful on unfinished tests')
    else:
        app.arg_parser.set_positional_metavar('TEST')
    if working_directory is not None:
        app.set_working_directory(working_directory)
    app.set_argv(args)
    app.set_report_stream(report_stream)
    app.enable_interactive()
    collected = []
    try:
        with app:
            if app_callback is not None:
                app_callback(app)
            try:
                with handling_exceptions():
                    if is_parallel() and app.parsed_args.interactive:
                        raise InteractiveParallelNotAllowed("Cannot run interactive mode in parallel")
                    if config.root.tmux.enabled and not is_child():
                        _logger.notice("About to start slash in new tmux session...")
                        run_slash_in_tmux(args)
                    if is_child():
                        worker = Worker(config.root.parallel.worker_id, app.session.id)
                        worker.connect_to_server()
                    if resume or rerun:
                        session_ids = app.positional_args
                        if not session_ids:
                            session_ids = [get_last_resumeable_session_id()]
                        get_successful_tests = False if resume else True
                        to_resume = [x for session_id in session_ids for x in \
                                     get_tests_from_previous_session(session_id, get_successful_tests=get_successful_tests)]
                        collected = app.test_loader.get_runnables(to_resume, prepend_interactive=app.parsed_args.interactive)
                    else:
                        collected = _collect_tests(app, args)

                collected = list(collected)
                if is_child():
                    worker.start_execution(app, collected)
                else:
                    with app.session.get_started_context():
                        report_tests_to_backslash(collected)
                        if is_parent():
                            app.session.parallel_manager = ParallelManager(args)
                            app.session.parallel_manager.start_server_in_thread(collected)
                            app.session.parallel_manager.start()
                        else:
                            run_tests(collected)

            finally:
                if not is_child():
                    save_resume_state(app.session.results)
                    clean_old_entries()
            if app.exit_code == 0 and not app.session.results.is_success(allow_skips=True):
                app.set_exit_code(-1)
    except Exception:         # pylint: disable=broad-except
        # Error reporting happens in app context
        assert app.exit_code != 0

    return app

slash_resume = functools.partial(slash_run, resume=True)
slash_rerun = functools.partial(slash_run, rerun=True)

def is_parallel():
    return config.root.parallel.num_workers

def is_child():
    return config.root.parallel.worker_id is not None

def is_parent():
    return is_parallel() and not is_child()

def report_tests_to_backslash(tests):
    active_plugins = manager.get_active_plugins()
    backslash_plugin = active_plugins.get('backslash', None)
    if backslash_plugin and hasattr(backslash_plugin, 'report_planned_tests'):
        backslash_plugin.report_planned_tests(tests)

def _collect_tests(app, args):  # pylint: disable=unused-argument
    paths = app.positional_args

    paths = _extend_paths_from_suite_files(paths)

    if not paths and not app.parsed_args.interactive:
        paths = config.root.run.default_sources

    if not paths and not app.parsed_args.interactive:
        raise CannotLoadTests("No tests specified")

    collected = app.test_loader.get_runnables(paths, prepend_interactive=app.parsed_args.interactive)
    if not collected:
        raise CannotLoadTests("No tests could be collected")

    return collected

def _extend_paths_from_suite_files(paths):
    suite_files = config.root.run.suite_files
    if not suite_files:
        return paths
    paths = list(paths)
    paths.extend(iter_suite_file_paths(suite_files))
    return paths
