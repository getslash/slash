import logbook, six

class SessionWarnings(object):
    def __init__(self):
        super(SessionWarnings, self).__init__()
        self.records = []

class WarnHandler(logbook.Handler, logbook.StringFormatterHandlerMixin):
    """
    Like a stream handler but keeps the values in memory. 
    This logger provides some ways to store warnings to log again at the end of the session.
    """
    default_format_string = six.u('[{record.time:%Y-%m-%d %H:%M}] '
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
        self.records.append(self.format(record))
