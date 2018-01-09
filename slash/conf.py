# pylint: disable=line-too-long
import logbook
from confetti import Config
from .utils.conf_utils import Doc, Cmdline

__all__ = ["config"]

config = Config({
    "debug": {
        "debug_skips": False // Doc("Enter pdb also for SkipTest exceptions"),
        "debug_hook_handlers": False // Doc("Enter pdb also for every exception encountered in a hook/callback. Only relevant when debugging is enabled"),
        "enabled": False // Doc("Enter pdb on failures and errors") // Cmdline(on="--pdb"),
        "filter_strings": [] // Doc("A string filter, selecting if to enter pdb") // Cmdline(append='--pdb-filter',
                                                                                             metavar='FILTER'),
        "debugger": None,
    },

    "log": {
        "colorize": False // Doc("Emit log colors to files"),
        "console_theme": {
            'inline-file-end-fail': 'red',
            'inline-file-end-skip': 'yellow',
            'inline-file-end-success': 'green',
            'inline-error': 'red',
            'inline-test-interrupted': 'yellow',
            'error-cause-marker': 'white/bold',
            'fancy-message': 'yellow/bold',
            'frame-local-varname': 'yellow/bold',
            'session-summary-success': 'green/bold',
            'session-summary-failure': 'red/bold',
            'error-separator-dash': 'red',
            'tb-error-message': 'red/bold',
            'tb-error': 'red/bold',
            'tb-frame-location': 'white/bold',
            'test-additional-details-header': 'black/bold',
            'test-additional-details': 'black/bold',
            'test-error-header': 'white',
            'test-skip-message': 'yellow',
            'tb-line-cause': 'white',
            'tb-test-line': 'red/bold',
            'tb-line': 'black/bold',
        },

        "console_level": logbook.WARNING // Cmdline(decrease='-v',
                                                    decrease_doc='Make console more verbose (can be specified multiple times)',
                                                    increase='-q',
                                                    increase_doc='Make console less verbose (can be specified multiple times)'),
        "color_console": None // Cmdline(on='--force-color', off='--no-color'),
        "traceback_variables": False // Doc("Logs values of variables in traceback frames for added errors"),
        "traceback_level": 2 // Doc("Detail level of tracebacks") // Cmdline(arg="--tb"),
        "truncate_console_lines": True // Doc("truncate long log lines on the console") // Cmdline(arg='--truncate-console-lines', metavar='yes/no'),
        "truncate_console_errors": False // Doc("If truncate_console_lines is set, also truncate long log lines, including and above the \"error\" level, on the console"),
        "root": None // Doc("Root directory for logs") // Cmdline(arg="-l", metavar="DIR"),
        "subpath": "{context.session.id}/{context.test_id}/debug.log" // Doc("Path to write logs to under the root"),
        "session_subpath": "{context.session.id}/session.log",
        "errors_subpath": None // Doc("Depreacted - Use 'highlights_subpath' config instead"),
        "highlights_subpath": None // Doc("If set, this path will be used to record highlights (eg. errors added) in the session and/or tests"),
        "last_session_symlink": None // Doc("If set, specifies a symlink path to the last session log file in each run"),
        "last_session_dir_symlink": None // Doc("If set, specifies a symlink path to the last session log directory"),
        "last_test_symlink": None // Doc("If set, specifies a symlink path to the last test log file in each run"),
        "last_failed_symlink": None // Doc("If set, specifies a symlink path to the last failed test log file"),
        "show_manual_errors_tb": True // Doc("Show tracebacks for errors added via slash.add_error"),
        "silence_loggers": [] // Doc("Logger names to silence"),
        "format": None // Doc("Format of the log line, as passed on to logbook. None will use the default format"),
        "console_format": None // Doc("Optional format to be used for console output. Defaults to the regular format"),
        "localtime": False // Doc("Use local time for logging. If False, will use UTC"),
        "unittest_mode": False // Doc("Used during unit testing. Emit all logs to stderr as well as the log files"),
        "unified_session_log": False // Doc("Make the session log file contain all logs, including from tests"),
    },
    "run": {
        "dump_variation": False // Doc("Output the full variation structure before each test is run (mainly used for internal debugging)"),
        "default_sources": [] // Doc("Default tests to run assuming no other sources are given to the runner"),
        "suite_files": [] // Doc("File(s) to be read for lists of tests to be run") // Cmdline(append="-f", metavar="FILENAME"),
        "stop_on_error": False // Doc("Stop execution when a test doesn't succeed") // Cmdline(on="-x"),
        "filter_strings": [] // Doc("A string filter, selecting specific tests by string matching against their name") // Cmdline(append='-k', metavar='FILTER'),
        "repeat_each": 1 // Doc("Repeat each test a specified amount of times") // Cmdline(arg='--repeat-each', metavar="NUM_TIMES"),
        "repeat_all": 1 // Doc("Repeat all suite a specified amount of times") // Cmdline(arg='--repeat-all', metavar="NUM_TIMES"),
        "session_state_path": "~/.slash/last_session" // Doc("Where to keep last session serialized data"),
        "project_customization_file_path": "./.slashrc",
        "user_customization_file_path": "~/.slash/slashrc",
        "message_assertion_introspection": True // Doc("When False, failing assertions which have messages attached will not emit introspection info"),
    },
    "parallel": {
        "num_workers": 0 // Doc("Parallel execution") // Cmdline(arg='--parallel', metavar="NUM_WORKERS"),
        "worker_id": None // Doc("Worker_id") // Cmdline(arg='--parallel-worker-id', metavar="WORKER_ID"),
        "server_addr": "localhost" // Doc("Server address") // Cmdline(arg='--parallel-addr', metavar="PARALLEL_SERVER_ADDRESS"),
        "server_port": 0 // Doc("Server port") // Cmdline(arg='--parallel-port', metavar="PARALLEL_SERVER_PORT"),
        "parent_session_id": None // Doc("parent session id") // Cmdline(arg='--parallel-parent-session-id', metavar="MASTER_SESSION_ID"),
        "communication_timeout_secs": 60 // Doc("timeout of worker in seconds"),
        "worker_connect_timeout": 10 // Doc("timeout for each worker to connect"),
        "no_request_timeout": 20 // Doc("timeout for server not getting requests"),
        "worker_error_file": "errors-worker" // Doc("worker error filename template"),
        "workers_error_dir": None // Doc("workers error directory") // Cmdline(arg='--workers-error-dir', metavar="WORKERS_ERROR_DIR"),
    },
    "tmux": {
        "enabled": False // Doc("Run inside tmux") // Cmdline(on="--tmux"),
        "use_panes": False // Doc("In parallel mode, run children inside panes and not windows") // Cmdline(on="--tmux-panes"),
    },
    "sentry": {
        "dsn": None // Doc("Possible DSN for a sentry service to log swallowed exceptions. "
                           "See http://getsentry.com for details"),
    },
    "plugins": {
        "search_paths": [] // Doc("List of paths in which to search for plugin modules"),
    },

    "plugin_config": {
        # DO NOT store configuration here. It is intended for dynamically loaded plugins
    },
})
