from . import context
from .conf import config
from .utils.path import ensure_containing_directory
from .warnings import WarnHandler
from contextlib import contextmanager
import logbook  # pylint: disable=F0401
import logbook.more
from ._compat import ExitStack
import os

_logger = logbook.Logger(__name__)

_custom_colors = {}

def set_log_color(logger_name, level, color):
    """Sets the color displayed in the console, according to the logger name and level
    """
    _custom_colors[logger_name, level] = color

class ConsoleHandler(logbook.more.ColorizedStderrHandler):

    MAX_LINE_LENGTH = 120

    def get_color(self, record):
        returned = _custom_colors.get((record.channel, record.level))
        if returned is None:
            returned = super(ConsoleHandler, self).get_color(record)
        return returned

    def format(self, record):
        result = super(ConsoleHandler, self).format(record)
        if len(result) > self.MAX_LINE_LENGTH:
            result = "\n".join(
                self._truncate(line) for line in result.splitlines())
        return result

    def _truncate(self, line):
        if len(line) > self.MAX_LINE_LENGTH:
            line = line[:self.MAX_LINE_LENGTH - 3] + "..."
        return line

    def emit(self, record):
        context.session.reporter.notify_before_console_output()
        returned = super(ConsoleHandler, self).emit(record)
        context.session.reporter.notify_after_console_output()
        return returned

class SessionLogging(object):
    """
    A context creator for logging within a session and its tests
    """
    def __init__(self, session):
        super(SessionLogging, self).__init__()
        self.warnings_handler = WarnHandler(session.warnings)
        self.console_handler = ConsoleHandler(bubble=True, level=config.root.log.console_level)
        self.session_log_path = self.test_log_path = None
        self._set_formatting(self.console_handler)

    @contextmanager
    def get_test_logging_context(self):
        with self._get_file_logging_context(config.root.log.subpath, config.root.log.last_test_symlink) as path:
            self.test_log_path = path
            yield path

    @contextmanager
    def get_session_logging_context(self):
        with self._get_file_logging_context(
            config.root.log.session_subpath, config.root.log.last_session_symlink) as path:
            self.session_log_path = path
            yield path

    @contextmanager
    def _get_file_logging_context(self, filename_template, symlink):
        with ExitStack() as stack:
            handler, path = self._get_file_log_handler(filename_template, symlink)
            stack.enter_context(handler)
            stack.enter_context(self.console_handler)
            stack.enter_context(self.warnings_handler)
            stack.enter_context(self._get_silenced_logs_context())
            for extra_handler in _extra_handlers:
                stack.enter_context(extra_handler)
            yield path

    def _get_silenced_logs_context(self):
        if not config.root.log.silence_loggers:
            return ExitStack()
        return SilencedLoggersHandler(config.root.log.silence_loggers)

    def _get_file_log_handler(self, subpath, symlink):
        root_path = config.root.log.root
        if root_path is None:
            log_path = None
            handler = logbook.NullHandler(bubble=False)
        else:
            log_path = os.path.join(root_path, subpath.format(context=context))
            ensure_containing_directory(log_path)
            handler = logbook.FileHandler(log_path, bubble=False)
            self._try_create_symlink(log_path, symlink)
            self._set_formatting(handler)
        return handler, log_path

    def _try_create_symlink(self, path, symlink):
        if symlink is None:
            return

        try:
            ensure_containing_directory(symlink)

            if os.path.exists(symlink):
                os.unlink(symlink)
            os.symlink(path, symlink)

        except Exception:  # pylint: disable=broad-except
            _logger.debug("Failed to create symlink {0} --> {1}", path, symlink, exc_info=True)

    def _set_formatting(self, handler):
        if config.root.log.localtime:
            logbook.set_datetime_format("local")
        fmt = config.root.log.format
        if fmt is not None:
            handler.format_string = fmt

class SilencedLoggersHandler(logbook.Handler):
    def __init__(self, silence_logger_names):
        super(SilencedLoggersHandler, self).__init__(bubble=False)
        self._silenced_names = set(silence_logger_names)
    def should_handle(self, record):
        return record.channel in self._silenced_names

def add_log_handler(handler):
    """
    Adds a log handler to be entered for sessions and for tests
    """
    _extra_handlers.append(handler)

def remove_all_extra_handlers():
    del _extra_handlers[:]

_extra_handlers = []

class VERBOSITIES(object):

    DEBUG = logbook.DEBUG
    INFO = logbook.INFO
    NOTICE = logbook.NOTICE
    WARNING = logbook.WARNING
    ERROR = logbook.ERROR
    CRITICAL = logbook.CRITICAL
