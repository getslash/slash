from . import context
from .conf import config
from contextlib import contextmanager
from .utils.path import ensure_containing_directory
import logbook # pylint: disable=F0401
import os

@contextmanager
def get_test_logging_context():
    handler = _get_log_handler(config.root.log.subpath)
    with handler:
        yield

@contextmanager
def get_session_logging_context():
    handler = _get_log_handler(config.root.log.suite_subpath)
    with handler:
        yield

def _get_log_handler(subpath):
    root_path = config.root.log.root
    if root_path is None:
        handler = logbook.NullHandler()
    else:
        log_path = os.path.join(root_path, subpath.format(context=context))
        ensure_containing_directory(log_path)
        handler = logbook.FileHandler(log_path, bubble=False)
    return handler
