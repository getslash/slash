import logbook
from confetti import Config
from .utils.conf_utils import Doc, Cmdline

__all__ = ["config"]

config = Config({
    "debug": {
        "debug_skips": False // Doc("Enter pdb also for SkipTest exceptions"),
        "debug_hook_handlers": False // Doc("Enter pdb also for every exception encountered in a hook/callback. Only relevant when debugging is enabled"),
        "enabled": False // Doc("Enter pdb on failures and errors") // Cmdline(on="--pdb"),
    },
    "log": {
        "console_level": logbook.WARNING // Doc("console log level (can be repeated). Higher log level means quieter output.") // Cmdline(decrease="-v", increase="-q"),
        "root": None // Doc("Root directory for logs") // Cmdline(arg="-l", metavar="DIR"),
        "subpath": "{context.session.id}/{context.test_id}/log" // Doc("Path to write logs to under the root"),
        "session_subpath": "{context.session.id}/session.log",
        "last_session_symlink": None // Doc("If set, saves a symlink to the last session log file in each run"),
        "last_test_symlink": None // Doc("If set, saves a symlink to the last test log file in each run"),
        "silence_loggers": [] // Doc("Logger names to silence"),
        "format": None // Doc("Format of the log line, as passed on to logbook. None will use the default format"),
        "localtime": False // Doc("Use local time for logging. If False, will use UTC"),
    },
    "run": {
        "default_sources": [] // Doc("Default tests to run assuming no other sources are given to the runner"),
        "suite_files": [] // Doc("File(s) to be read for lists of tests to be run") // Cmdline(append="-f", metavar="FILENAME"),
        "stop_on_error": False // Doc("Stop execution when a test doesn't succeed") // Cmdline(on="-x"),
        "session_state_path": "~/.slash/last_session" // Doc("Where to keep last session serialized data"),
        "user_customization_file_path": "~/.slash/slashrc",
    },
    "sentry": {
        "dsn": None // Doc("Possible DSN for a sentry service to log swallowed exceptions. "
                           "See http://getsentry.com for details"),
    },
    "plugins": {
        "search_paths": [] // Doc("List of paths in which to search for plugin modules"),
    },
})
