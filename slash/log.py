import datetime
import numbers
import os
import sys
from contextlib import contextmanager, closing

import logbook  # pylint: disable=F0401
import logbook.more
from vintage import warn_deprecation

from . import context
from ._compat import ExitStack
from .conf import config
from .utils.path import ensure_containing_directory
from .warnings import WarnHandler
from .exceptions import InvalidConfiguraion
from .exception_handling import handling_exceptions
from . import hooks

_logger = logbook.Logger(__name__)

_custom_colors = {}
filtered_channels = {'slash.runner', 'slash.loader', 'slash.core.cleanup_manager', 'slash.core.scope_manager', \
                      'slash.exception_handling', 'slash.core.fixtures.fixture_store'}

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
        if config.root.log.color_console is not None:
            if config.root.log.color_console:
                self.force_color()
            else:
                self.forbid_color()

    def format(self, record):
        orig_message = record.message
        should_truncate = self._truncate_errors or record.level < logbook.ERROR
        if self._truncate_lines and len(str(orig_message)) > self.MAX_LINE_LENGTH and should_truncate:
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
        reporter = None if context.session is None else context.session.reporter
        if reporter is not None:
            reporter.notify_before_console_output()
        returned = super(ConsoleHandler, self).emit(record)
        if reporter is not None:
            reporter.notify_after_console_output()
        return returned

def _slash_logs_filter(record, handler): # pylint: disable=unused-argument
    return record.extra.get('filter_bypass') or \
           record.channel not in filtered_channels or \
           record.level >= config.root.log.core_log_level

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
        self.console_handler = ConsoleHandler(bubble=True, level=config.root.log.console_level, stream=console_stream, filter=_slash_logs_filter)
        #: contains the path for the session logs
        self.session_log_path = None
        self.session_log_handler = None
        #: contains the path for the current test logs
        self.test_log_path = None
        self._set_formatting(self.console_handler, config.root.log.console_format or config.root.log.format)
        self._log_path_to_handler = {}

    def get_active_log_paths(self):
        return [log_path for log_path, handler in self._log_path_to_handler.items() if handler is not None]

    @contextmanager
    def get_test_logging_context(self, result):
        with self._get_file_logging_context(config.root.log.subpath, config.root.log.last_test_symlink) as (_, path):
            self.test_log_path = path
            result.set_log_path(path)
            try:
                yield path
            finally:
                self._create_last_failed_symlink_if_needed(result)

    def _create_last_failed_symlink_if_needed(self, result):
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
            handler = stack.enter_context(self._log_file_handler_context(filename_template, symlink, \
                                                                         use_compression=config.root.log.compression.enabled))
            stack.enter_context(handler.applicationbound())
            if config.root.log.compression.enabled and config.root.log.compression.use_rotating_raw_file:
                rotating_handler = stack.enter_context(self._log_file_handler_context(filename_template, symlink, bubble=True, use_rotation=True))
                stack.enter_context(rotating_handler.applicationbound())

            stack.enter_context(self.console_handler.applicationbound())
            stack.enter_context(self.warnings_handler.applicationbound())
            error_handler = stack.enter_context(self._get_error_logging_context())
            stack.enter_context(error_handler.applicationbound())
            stack.enter_context(self._get_silenced_logs_context())
            if config.root.log.unittest_mode:
                stack.enter_context(logbook.StreamHandler(sys.stderr, bubble=True, level=logbook.TRACE))
            for extra_handler in _extra_handlers:
                stack.enter_context(extra_handler.applicationbound())
            if config.root.log.unified_session_log and self.session_log_handler is not None:
                stack.enter_context(_make_bubbling_handler(self.session_log_handler))

            path = handler.stream.name if isinstance(handler, logbook.FileHandler) else None
            yield handler, path


    def _should_delete_log(self, result):
        return (not config.root.log.cleanup.keep_failed) or \
               (not result.is_global_result() and result.is_success(allow_skips=True)) or \
               (result.is_global_result() and self.session.results.is_success(allow_skips=True))

    @contextmanager
    def _get_error_logging_context(self):
        with ExitStack() as stack:
            path = config.root.log.errors_subpath
            if path:
                warn_deprecation('log.errors_subpath configuration is deprecated since 1.5.0. '
                                 'Please use log.highlights_subpath instead')
            else:
                path = config.root.log.highlights_subpath
            def _error_added_filter(record, handler): # pylint: disable=unused-argument
                return record.extra.get('highlight')

            handler = stack.enter_context(self._log_file_handler_context(path, symlink=None, bubble=True, filter=_error_added_filter))
            log_path = handler.stream.name if isinstance(handler, logbook.FileHandler) else None
            if log_path and self.session.results.current is self.session.results.global_result:
                self.session.results.global_result.add_extra_log_path(log_path)
            yield handler

    def _get_silenced_logs_context(self):
        if not config.root.log.silence_loggers:
            return ExitStack()
        return SilencedLoggersHandler(config.root.log.silence_loggers).applicationbound()

    def _get_log_file_path(self, subpath, use_compression):
        log_path = self._normalize_path(os.path.join(config.root.log.root, _format_log_path(subpath)))
        if use_compression:
            if config.root.log.compression.algorithm == "gzip":
                log_path += ".gz"
            elif config.root.log.compression.algorithm == "brotli":
                log_path += ".br"
            else:
                raise InvalidConfiguraion("Unsupported compression method: {}".format(config.root.log.compression.algorithm))
        return log_path

    def _create_log_file_handler(self, log_path, bubble=False, filter=_slash_logs_filter, use_compression=False, use_rotation=False):
        kwargs = {"bubble": bubble, "filter": filter}
        if use_compression:
            if config.root.log.compression.algorithm == "gzip":
                handler_class = logbook.GZIPCompressionHandler
            elif config.root.log.compression.algorithm == "brotli":
                handler_class = logbook.BrotliCompressionHandler
        elif use_rotation:
            kwargs.update({"max_size": 4*1024**2, "backup_count": 1})
            handler_class = logbook.RotatingFileHandler
        elif config.root.log.colorize:
            handler_class = ColorizedFileHandler
        else:
            handler_class = logbook.FileHandler
        return handler_class(log_path, **kwargs)

    @contextmanager
    def _log_file_handler_context(self, subpath, symlink, bubble=False, filter=_slash_logs_filter, use_compression=False, use_rotation=False):
        if subpath is None or config.root.log.root is None:
            yield NoopHandler() if bubble else logbook.NullHandler(filter=filter)
        else:
            log_path = self._get_log_file_path(subpath, use_compression)
            handler = self._log_path_to_handler.get(log_path, None)
            if handler is not None:
                yield handler
            else:
                result = context.result
                ensure_containing_directory(log_path)
                if symlink:
                    self._try_create_symlink(log_path, symlink)
                with closing(self._create_log_file_handler(log_path, bubble=bubble, use_compression=use_compression, \
                                                           use_rotation=use_rotation, filter=filter)) as handler:
                    self._log_path_to_handler[log_path] = handler
                    self._set_formatting(handler, config.root.log.format)
                    yield handler
                self._log_path_to_handler[log_path] = None
                hooks.log_file_closed(path=log_path, result=result)  # pylint: disable=no-member
                if config.root.log.cleanup.enabled and self._should_delete_log(result):
                    with handling_exceptions(swallow=True):
                        os.remove(log_path)
                        dir_path = os.path.dirname(log_path)
                        if not os.listdir(dir_path) and dir_path != self._normalize_path(config.root.log.root):
                            os.rmdir(dir_path)


    def _normalize_path(self, p):
        return os.path.expanduser(p)

    def create_worker_symlink(self, worker_name, worker_session_id):
        if config.root.log.root is None:
            return
        symlink = os.path.join(self.session.id, worker_name)
        worker_dir = os.path.join(self._normalize_path(config.root.log.root), worker_session_id)
        self._try_create_symlink(worker_dir, symlink)

    def _try_create_symlink(self, path, symlink):
        if symlink is None or config.root.log.root is None or config.root.parallel.worker_id is not None:
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

class NoopHandler(object):

    # Logbook's NullHandler does not bubble by default. This is dummy handler that
    # does not interfere with the stack at all
    def applicationbound(self):
        return ExitStack()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

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


def _make_bubbling_handler(handler):
    return _BubblingWrapper(handler)

class _BubblingWrapper(logbook.Handler):

    def __init__(self, handler):
        super(_BubblingWrapper, self).__init__(bubble=True)
        self._handler = handler
        self.should_handle = self._handler.should_handle
        self.handle = self._handler.handle


def _format_log_path(p):
    return p.format(context=_NormalizedObject(context), timestamp=datetime.datetime.now())


class RetainedLogHandler(logbook.TestHandler):
    """A logbook handler that retains the emitted logs in order to
    flush them later to a handler.

    This is useful to keep logs that are emitted during session configuration phase, and not lose
    them from the session log
    """
    def __init__(self, *args, **kwargs):
        super(RetainedLogHandler, self).__init__(*args, **kwargs)
        self._enabled = True

    def emit(self, record):
        if self._enabled:
            return super(RetainedLogHandler, self).emit(record)

    def flush_to_handler(self, handler):
        for r in self.records:
            if handler.should_handle(r):
                handler.emit(r)
        del self.records[:]

    def disable(self):
        self._enabled = False
