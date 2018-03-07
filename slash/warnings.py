from __future__ import absolute_import

import collections

import logbook
import warnings

from . import hooks
from .utils.warning_capture import warning_callback_context
from .ctx import context
from contextlib import contextmanager


_native_logger = logbook.Logger('slash.native_warnings')


class LogbookWarning(UserWarning):
    pass

class SessionWarnings(object):
    """
    Holds all warnings emitted during the session
    """
    def __init__(self):
        super(SessionWarnings, self).__init__()
        self.warnings = []

    @contextmanager
    def capture_context(self):
        warnings.simplefilter('always')
        warnings.filterwarnings('ignore', category=ImportWarning)

        with warning_callback_context(self._capture_native_warning):
            yield

    def _capture_native_warning(self, message, category, filename, lineno, file=None, line=None): # pylint: disable=unused-argument
        warning = RecordedWarning.from_native_warning(message, category, filename, lineno)
        for ignored_warning in _ignored_warnings:
            if ignored_warning.matches(warning):
                return
        self.add(warning)
        if not issubclass(category, LogbookWarning):
            _native_logger.warning('{filename}:{lineno}: {warning!r}', filename=filename, lineno=lineno, warning=warning)

    def add(self, warning):
        hooks.warning_added(warning=warning) # pylint: disable=no-member
        self.warnings.append(warning)

    def __iter__(self):
        "Iterates through stored warnings"
        return iter(self.warnings)

    def __len__(self):
        return len(self.warnings)

    def __nonzero__(self):
        return bool(self.warnings)

    __bool__ = __nonzero__


class WarnHandler(logbook.Handler, logbook.StringFormatterHandlerMixin):
    """
    Like a stream handler but keeps the values in memory.
    This logger provides some ways to store warnings to log again at the end of the session.
    """
    default_format_string = (u'[{record.time:%Y-%m-%d %H:%M}] '
      '{record.level_name}: {record.extra[source]}: {record.message}')
    def __init__(self, session_warnings, format_string=None, filter=None, bubble=True):
        logbook.Handler.__init__(self, logbook.WARNING, filter, bubble)
        logbook.StringFormatterHandlerMixin.__init__(self, format_string)
        self.session_warnings = session_warnings

    def should_handle(self, record):
        """Returns `True` if this record is a warning """
        if record.channel == _native_logger.name:
            return False
        return record.level == self.level

    def emit(self, record):
        warnings.warn_explicit(message=record.message, category=LogbookWarning, filename=record.filename,
                               lineno=record.lineno, module=record.module)


WarningKey = collections.namedtuple("WarningKey", ("filename", "lineno"))

class RecordedWarning(object):

    def __init__(self, details, message, category=None):
        super(RecordedWarning, self).__init__()
        self.details = details
        self.details['session_id'] = context.session_id
        self.details['test_id'] = context.test_id
        self.details.setdefault('func_name', None)
        self.key = WarningKey(filename=self.details['filename'], lineno=self.details['lineno'])
        self.category = category
        self._repr = message

    @classmethod
    def from_log_record(cls, record, handler):
        details = record.to_dict()
        return cls(details, handler.format(record))


    @classmethod
    def from_native_warning(cls, message, category, filename, lineno):
        if isinstance(message, Warning):
            message = message.args[0]

        return cls({
            'message': message,
            'type': category.__name__,
            'filename': filename,
            'lineno': lineno,
            }, message=message, category=category)

    @property
    def message(self):
        return self.details.get('message')

    @property
    def lineno(self):
        return self.details.get('lineno')

    @property
    def filename(self):
        return self.details.get('filename')


    def to_dict(self):
        return self.details.copy()

    def __repr__(self):
        return self._repr

class _IgnoredWarning(object):

    def __init__(self, category, filename, lineno, message):
        self.category = category
        self.filename = filename
        self.lineno = lineno
        self.message = message

    def matches(self, warning):
        if self.category is not None and issubclass(warning.category, self.category):
            return True

        if self.filename is not None and warning.filename == self.filename:
            return True

        if self.lineno is not None and warning.lineno == self.lineno:
            return True

        if self.message is not None:
            if hasattr(self.message, 'match'):
                if self.message.match(warning.message):
                    return True
            elif self.message == warning.message:
                return True
        return False

_ignored_warnings = []


def ignore_warnings(category=None, message=None, filename=None, lineno=None):
    """
    Ignores warnings of specific origin (category/filename/lineno/message) during the session. Unlike
    Python's default ``warnings.filterwarnings``, the parameters are matched only if specified (not defaulting to "match all"). Message can also be a
    regular expression object compiled with ``re.compile``.

        slash.ignore_warnings(category=CustomWarningCategory)
    """
    _ignored_warnings.append(_IgnoredWarning(category=category, filename=filename, lineno=lineno, message=message))


def clear_ignored_warnings():
    del _ignored_warnings[:]
