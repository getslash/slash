import sys

from . import context
from .conf import config
from .utils.path import ensure_containing_directory
from .warnings import WarnHandler
from contextlib import contextmanager
import logbook  # pylint: disable=F0401
import logbook.more
from ._compat import ExitStack
import os
import numbers

_logger = logbook.Logger(__name__)

_custom_colors = {}


class _NormalizedObject(object):
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        obj = getattr(self._obj, name)
        return obj if isinstance(obj, numbers.Number) else _NormalizedObject(obj)

    @staticmethod
    def _escape(s):
        return s.replace('\\', '_').replace('/', '_')

    def __str__(self):
        return self._escape(str(self._obj))

    def __repr__(self):
        return self._escape(repr(self._obj))


def set_log_color(logger_name, level, color):
    """Sets the color displayed in the console, according to the logger name and level
    """
    _custom_colors[logger_name, level] = color

class ColorizedHandlerMixin(logbook.more.ColorizingStreamHandlerMixin):

    def get_color(self, record):
        returned = _custom_colors.get((record.channel, record.level))
        if returned is not None:
            return returned

        if record.level >= logbook.ERROR:
            return 'red'
        elif record.level >= logbook.WARNING:
            return 'yellow'
        elif record.level >= logbook.NOTICE:
            return 'white'
        return None # default

class ColorizedFileHandler(ColorizedHandlerMixin, logbook.FileHandler):

    def should_colorize(self, record):
        return True


class ConsoleHandler(ColorizedHandlerMixin, logbook.StreamHandler):

    MAX_LINE_LENGTH = 160

    default_format_string = '[{record.time:%Y-%m-%d %H:%M:%S}] {record.message}'

    def __init__(self, **kw):
        stream = kw.pop('stream', sys.stderr)
        logbook.StreamHandler.__init__(self, stream=stream, **kw)
        self._truncate_lines = config.root.log.truncate_console_lines
        self._truncate_errors = config.root.log.truncate_console_errors


    def format(self, record):
        orig_message = record.message
        should_truncate = self._truncate_errors or record.level < logbook.ERROR
        if self._truncate_lines and len(orig_message) > self.MAX_LINE_LENGTH and should_truncate:
            record.message = "\n".join(self._truncate(line) for line in orig_message.splitlines())
        try:
            returned = super(ConsoleHandler, self).format(record)
        finally:
            # we back up the original message to avoid propagating truncated lines into the file log
            record.message = orig_message
        return returned

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
    def __init__(self, session, console_stream=None):
        super(SessionLogging, self).__init__()
        if console_stream is None:
            console_stream = sys.stderr
        self.session = session
        self.warnings_handler = WarnHandler(session.warnings)
        self.console_handler = ConsoleHandler(bubble=True, level=config.root.log.console_level, stream=console_stream)
        #: contains the path for the session logs
        self.session_log_path = None
        self.session_log_handler = None
        #: contains the path for the current test logs
        self.test_log_path = None
        self._set_formatting(self.console_handler, config.root.log.console_format or config.root.log.format)

    @contextmanager
    def get_test_logging_context(self):
        with self._get_file_logging_context(config.root.log.subpath, config.root.log.last_test_symlink) as (_, path):
            self.test_log_path = path
            context.result.set_log_path(path)
            try:
                yield path
            finally:
                self._create_last_failed_symlink_if_needed()

    def _create_last_failed_symlink_if_needed(self):
        result = context.result
        assert result
        if result.is_error() or result.is_failure():
            self._try_create_symlink(result.get_log_path(), config.root.log.last_failed_symlink)

    @contextmanager
    def get_session_logging_context(self):
        assert self.session_log_handler is None
        with self._get_file_logging_context(
            config.root.log.session_subpath, config.root.log.last_session_symlink) as (handler, path):
            self.session_log_handler = handler
            self.session_log_path = path
            self.session.results.global_result.set_log_path(path)
            if config.root.log.last_session_dir_symlink is not None and self.session_log_path is not None:
                self._try_create_symlink(os.path.dirname(self.session_log_path), config.root.log.last_session_dir_symlink)
            yield path

    @contextmanager
    def _get_file_logging_context(self, filename_template, symlink):
        with ExitStack() as stack:
            handler, path = self._get_file_log_handler(filename_template, symlink)
            stack.enter_context(handler.applicationbound())
            stack.enter_context(self.console_handler.applicationbound())
            stack.enter_context(self.warnings_handler.applicationbound())
            stack.enter_context(self._get_silenced_logs_context())
            if config.root.log.unittest_mode:
                stack.enter_context(logbook.StreamHandler(sys.stderr, bubble=True))
            for extra_handler in _extra_handlers:
                stack.enter_context(extra_handler.applicationbound())
            if config.root.log.unified_session_log and self.session_log_handler is not None:
                stack.enter_context(self.session_log_handler)

            yield handler, path

    def _get_silenced_logs_context(self):
        if not config.root.log.silence_loggers:
            return ExitStack()
        return SilencedLoggersHandler(config.root.log.silence_loggers).applicationbound()

    def _get_file_log_handler(self, subpath, symlink):
        root_path = config.root.log.root
        if root_path is None:
            log_path = None
            handler = logbook.NullHandler()
        else:
            log_path = self._normalize_path(os.path.join(root_path, subpath.format(context=_NormalizedObject(context))))
            ensure_containing_directory(log_path)
            handler = self._get_file_handler_class()(log_path, bubble=False)
            self._try_create_symlink(log_path, symlink)
            self._set_formatting(handler, config.root.log.format)
        return handler, log_path

    def _get_file_handler_class(self):
        if config.root.log.colorize:
            return ColorizedFileHandler
        return logbook.FileHandler

    def _normalize_path(self, p):
        return os.path.expanduser(p)

    def _try_create_symlink(self, path, symlink):
        if symlink is None or config.root.log.root is None:
            return

        symlink = self._normalize_path(symlink)

        if not os.path.isabs(symlink):
            symlink = os.path.join(self._normalize_path(config.root.log.root), symlink)

        try:
            ensure_containing_directory(symlink)

            if os.path.exists(symlink) or os.path.islink(symlink):
                os.unlink(symlink)
            os.symlink(path, symlink)

        except Exception:  # pylint: disable=broad-except
            _logger.debug("Failed to create symlink {0} --> {1}", path, symlink, exc_info=True)

    def _set_formatting(self, handler, fmt):
        if config.root.log.localtime:
            logbook.set_datetime_format("local")
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
