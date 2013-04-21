from .formatter import Formatter
import itertools

_REPORT_COLUMNS = [
    ("Successful", "get_num_successful"),
    ("Failures", "get_num_failures"),
    ("Errors", "get_num_errors"),
    ("Skipped", "get_num_skipped"),
    ]

class Reporter(object):
    def __init__(self, stream):
        super(Reporter, self).__init__()
        self._formatter = Formatter(stream)
    def report_session(self, session):
        self._describe_unsuccessful(session)
        self._describe_summary(session)
    def _describe_unsuccessful(self, session):
        self._formatter.write_separator()
        for result in session.iter_results():
            if result.is_success():
                continue
            self._formatter.writeln("> ", result.test_metadata)
            with self._formatter.indented():
                for x in itertools.chain(result.get_failures(), result.get_errors()):
                    self._formatter.writeln(x)
    def _describe_summary(self, session):
        self._formatter.write_separator()
        for col, _ in _REPORT_COLUMNS:
            self._formatter.write(col.ljust(len(col)+2))
        self._formatter.writeln()
        for col, method_name in _REPORT_COLUMNS:
            self._formatter.write(str(getattr(session.result, method_name)()).ljust(len(col)+2))
        self._formatter.writeln()
