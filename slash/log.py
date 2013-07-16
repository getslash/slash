import os
import six
import logbook # pylint: disable=F0401
from . import context
from .conf import config
from .utils.path import ensure_containing_directory
from contextlib import contextmanager
from logbook.more import ColorizedStderrHandler # pylint: disable=F0401

@contextmanager
def get_test_logging_context():
    handler = _get_file_log_handler(config.root.log.subpath)
    with handler:
        with _get_console_handler():
            with _get_warning_handler():
                with _process_test_record():
                    yield

@contextmanager
def get_session_logging_context():
    handler = _get_file_log_handler(config.root.log.session_subpath)
    with handler:
        console_handler = _get_console_handler()
        with console_handler:
            with _get_warning_handler():
                with _process_test_record():
                    yield
            _log_warnings_before_session_close(console_handler)

def _get_console_handler():
    return ColorizedStderrHandler(bubble=True, level=config.root.log.console_level)

def _get_warning_handler():
    return context.session.warnings

def _log_warnings_before_session_close(console_handler):
    warn_handler = _get_warning_handler()
    console_handler.format_string = warn_handler.format_string
    for record in warn_handler.records:
        console_handler.handle(record)

def _get_file_log_handler(subpath):
    root_path = config.root.log.root
    if root_path is None:
        handler = logbook.NullHandler(bubble=False)
    else:
        log_path = os.path.join(root_path, subpath.format(context=context))
        ensure_containing_directory(log_path)
        handler = logbook.FileHandler(log_path, bubble=False)
    return handler

def _add_current_test(record):
    record.extra['source'] = context.test_id or context.session.id

def _process_test_record():
    return logbook.Processor(_add_current_test)

class WarnHandler(logbook.Handler, logbook.StringFormatterHandlerMixin):
    """
    Like a stream handler but keeps the values in memory. 
    This logger provides some ways to store warnings to log again at the end of the session.
    """
    default_format_string = six.u('[{record.time:%Y-%m-%d %H:%M}] '
      '{record.level_name}: {record.extra[source]}: {record.message}')

    def __init__(self, format_string=None, filter=None, bubble=True):
        logbook.Handler.__init__(self, logbook.WARNING, filter, bubble)
        logbook.StringFormatterHandlerMixin.__init__(self, format_string)
        #: captures the :class:`LogRecord`\s as instances
        self.records = []

    def close(self):
        """Close all records down when the handler is closed."""
        for record in self.records:
            record.close()

    def should_handle(self, record):
        """Returns `True` if this record is a warning """
        return record.level == self.level

    def emit(self, record):
        # keep records open because we will want to examine them after the
        # call to the emit function.  If we don't do that, the traceback
        # attribute and other things will already be removed.
        record.keep_open = True
        self.records.append(record)



