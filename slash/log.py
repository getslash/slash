from . import context
from .conf import config
from .utils.path import ensure_containing_directory
from contextlib import contextmanager
import logbook # pylint: disable=F0401
from logbook.more import ColorizedStderrHandler # pylint: disable=F0401
import os

@contextmanager
def get_test_logging_context():
    handler = _get_file_log_handler(config.root.log.subpath)
    with handler:
        with _get_console_handler():
            yield

@contextmanager
def get_session_logging_context():
    handler = _get_file_log_handler(config.root.log.session_subpath)
    with handler:
        with _get_console_handler():
            yield

def _get_console_handler():
    return ColorizedStderrHandler(bubble=True, level=config.root.log.console_level)

def _get_file_log_handler(subpath):
    root_path = config.root.log.root
    if root_path is None:
        handler = logbook.NullHandler(bubble=False)
    else:
        log_path = os.path.join(root_path, subpath.format(context=context))
        ensure_containing_directory(log_path)
        handler = logbook.FileHandler(log_path, bubble=False)
    return handler
