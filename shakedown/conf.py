import logbook
from confetti import Config
from .utils.conf_utils import Doc, Cmdline

__all__ = ["config"]

config = Config({
    "debug" : {
        "enabled" : False // Doc("Enter pdb on failures and errors") // Cmdline(on="--pdb"),
    },
    "log" : {
        "console_level" : logbook.WARNING // Doc("console verbosity") // Cmdline(decrease="-v", increase="-q"),
        "root" : None // Doc("Root directory for logs") // Cmdline(arg="-l"),
        "subpath" : "{context.session.id}/{context.test_id}/log" // Doc("Path to write logs to under the root"),
        "session_subpath" : "session.log",
    },
    "run" : {
        "stop_on_error" : False // Doc("Stop execution when a test doesn't succeed") // Cmdline(on="-x"),
    },
    "notifications" : {
        "prowl_api_key" : None,
        "nma_api_key" : None,
    },
    "sentry" : {
        "dsn" : None // Doc("Possible DSN for a sentry service to log swallowed exceptions. "
                            "See http://getsentry.com for details"),
    },
    "hooks" : {
        "swallow_exceptions" : False // Doc("If set, exceptions inside hooks will be re-raised"),
    },
    "plugins" : {
        "search_paths" : [] // Doc("List of paths in which to search for plugin modules"),
    },
})
