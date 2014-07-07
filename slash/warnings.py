import collections

import logbook

from .ctx import context


class SessionWarnings(object):
    """
    Holds all warnings emitted during the session
    """
    def __init__(self):
        super(SessionWarnings, self).__init__()
        self.records = []

    def __iter__(self):
        "Iterates through stored warnings"
        return iter(self.records)

    def __len__(self):
        return len(self.records)

    def __nonzero__(self):
        return bool(self.records)

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
        #: captures the :class:`LogRecord`\s as instances
        self.records = session_warnings.records

    def should_handle(self, record):
        """Returns `True` if this record is a warning """
        return record.level == self.level

    def emit(self, record):
        self.records.append(Warning(record, self.format(record)))

WarningKey = collections.namedtuple("WarningKey", ("filename", "lineno"))

class Warning(object):

    def __init__(self, record, message):
        super(Warning, self).__init__()
        self.details = record.to_dict()
        self.details['session_id'] = context.session_id
        self.details['test_id'] = context.test_id
        self.key = WarningKey(filename=self.details['filename'], lineno=self.details['lineno'])
        self._repr = message

    def to_dict(self):
        return self.details.copy()

    def __repr__(self):
        return self._repr
