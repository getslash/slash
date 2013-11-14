import logbook
from confetti import Config
from .utils.conf_utils import Doc, Cmdline

__all__ = ["config"]

config = Config({
    "debug" : {
        "debug_skips" : False // Doc("Enter pdb also for SkipTest exceptions"),
        "debug_hooks" : False // Doc("Enter pdb also for every exception encountered in a hook/callback"),
        "enabled" : False // Doc("Enter pdb on failures and errors") // Cmdline(on="--pdb"),
    },
    "log" : {
        "console_level" : logbook.WARNING // Doc("console verbosity (can be repeated)") // Cmdline(decrease="-v", increase="-q"),
        "root" : None // Doc("Root directory for logs") // Cmdline(arg="-l", metavar="DIR"),
        "subpath" : "{context.session.id}/{context.test_id}/log" // Doc("Path to write logs to under the root"),
        "session_subpath" : "session.log",
        "silence_loggers": [] // Doc("Logger names to silence"),
        "format": None // Doc("Format of the log line, as passed on to logbook. None will use the default format"),
        "localtime": False // Doc("Use local time for logging. If False, will use UTC"),
    },
    "run" : {
        "default_sources": [] // Doc("Default tests to run assuming no other sources are given to the runner"),
        "stop_on_error" : False // Doc("Stop execution when a test doesn't succeed") // Cmdline(on="-x"),
        "session_state_path": "~/.slash/last_session" // Doc("Where to keep last session serialized data"),
        "user_customization_file_path": "~/.slash/slashrc",
    },
    "sentry" : {
        "dsn" : None // Doc("Possible DSN for a sentry service to log swallowed exceptions. "
                            "See http://getsentry.com for details"),
    },
    "hooks" : {
        "swallow_exceptions" : False // Doc("If set, exceptions inside hooks will not be re-raised"),
    },
    "plugins" : {
        "search_paths" : [] // Doc("List of paths in which to search for plugin modules"),
    },
})
