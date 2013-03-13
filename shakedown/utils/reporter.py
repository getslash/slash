from .formatter import Formatter

_REPORT_COLUMNS = [
    ("Successful", "get_num_successful"),
    ("Failures", "get_num_failures"),
    ("Errors", "get_num_errors"),
    ]

class Reporter(object):
    def __init__(self, stream):
        super(Reporter, self).__init__()
        self._formatter = Formatter(stream)
    def report_suite(self, suite):
        self._formatter.writeln("Result Summary:")
        self._formatter.write_separator()
        for col, _ in _REPORT_COLUMNS:
            self._formatter.write(col.ljust(len(col)+2))
        self._formatter.writeln()
        for col, method_name in _REPORT_COLUMNS:
            self._formatter.write(str(getattr(suite.result, method_name)()).ljust(len(col)+2))
        self._formatter.writeln()
