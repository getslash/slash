from . import context
from .conf import config
from .utils.path import ensure_containing_directory
from .warnings import WarnHandler
from contextlib import contextmanager
import logbook # pylint: disable=F0401
from logbook.more import ColorizedStderrHandler # pylint: disable=F0401
from ._compat import ExitStack
import os

class SessionLogging(object):
    """
    A context creator for logging within a session and its tests
    """
    def __init__(self, session):
        super(SessionLogging, self).__init__()
        self.warnings_handler = WarnHandler(session.warnings)
        self.console_handler = ColorizedStderrHandler(bubble=True, level=config.root.log.console_level)

    def get_test_logging_context(self):
        return self._get_file_logging_context(config.root.log.subpath)

    def get_session_logging_context(self):
        return self._get_file_logging_context(config.root.log.session_subpath)

    @contextmanager
    def _get_file_logging_context(self, filename_template):
        with ExitStack() as stack:
            stack.enter_context(self._get_file_log_handler(filename_template))
            stack.enter_context(self.console_handler)
            stack.enter_context(self.warnings_handler)
            stack.enter_context(self._process_test_record())
            stack.enter_context(self._get_silenced_logs_context())
            yield

    def _get_silenced_logs_context(self):
        if not config.root.log.silence_loggers:
            return ExitStack()
        return SilencedLoggersHandler(config.root.log.silence_loggers)

    def _get_file_log_handler(self, subpath):
        root_path = config.root.log.root
        if root_path is None:
            handler = logbook.NullHandler(bubble=False)
        else:
            log_path = os.path.join(root_path, subpath.format(context=context))
            ensure_containing_directory(log_path)
            handler = logbook.FileHandler(log_path, bubble=False)
        return handler

    def _add_current_test(self, record):
        record.extra['source'] = context.test_id or context.session.id

    def _process_test_record(self):
        return logbook.Processor(self._add_current_test)

class SilencedLoggersHandler(logbook.Handler):
    def __init__(self, silence_logger_names):
        super(SilencedLoggersHandler, self).__init__(bubble=False)
        self._silenced_names = set(silence_logger_names)
    def should_handle(self, record):
        return record.channel in self._silenced_names
