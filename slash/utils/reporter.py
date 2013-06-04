import logbook
import itertools
from contextlib import contextmanager
from .formatter import Formatter
from .hooks_context_manager import HooksContextManager
from ..conf import config
from ..ctx import context

@contextmanager
def report_context(report_stream):
    live_reporter_type = ConciseLiveReporter if config.root.log.console_level > logbook.NOTICE \
                         else VerboseLiveReporter
    with live_reporter_type(report_stream):
        yield
    SummaryReporter(report_stream).report_session(context.session)

def _format_unsuccessfull(formatter, result):
    with formatter.indented():
        for x in itertools.chain(result.get_failures(), result.get_errors(), result.get_skips()):
            formatter.writeln(x)

_REPORT_COLUMNS = [
    ("Successful", "get_num_successful"),
    ("Failures", "get_num_failures"),
    ("Errors", "get_num_errors"),
    ("Skipped", "get_num_skipped"),
    ]

class SummaryReporter(object):
    def __init__(self, stream):
        super(SummaryReporter, self).__init__()
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
            _format_unsuccessfull(self._formatter, result)
    def _describe_summary(self, session):
        self._formatter.write_separator()
        for col, _ in _REPORT_COLUMNS:
            self._formatter.write(col.ljust(len(col)+2))
        self._formatter.writeln()
        for col, method_name in _REPORT_COLUMNS:
            self._formatter.write(str(getattr(session.result, method_name)()).ljust(len(col)+2))
        self._formatter.writeln()

class BaseLiveReporter(HooksContextManager):
    def __init__(self, report_stream):
        super(BaseLiveReporter, self).__init__()
        self._formatter = Formatter(report_stream)

class VerboseLiveReporter(BaseLiveReporter):
    def on_test_start(self):
        self._formatter.write("> ", context.test)
        self._formatter.write(" ... ")
    def on_test_success(self):
        self._formatter.writeln("ok")
    def on_test_error(self):
        self._formatter.writeln("error")
        _format_unsuccessfull(self._formatter, context.session.get_result(context.test))
    def on_test_failure(self):
        self._formatter.writeln("fail")
        _format_unsuccessfull(self._formatter, context.session.get_result(context.test))
    def on_test_skip(self):
        self._formatter.writeln("skip")
        _format_unsuccessfull(self._formatter, context.session.get_result(context.test))

class ConciseLiveReporter(BaseLiveReporter):
    def on_test_success(self):
        self._formatter.write(".")
    def on_test_error(self):
        self._formatter.write("E")
    def on_test_failure(self):
        self._formatter.write("F")
    def on_test_skip(self):
        self._formatter.write("S")
    def on_result_summary(self):
        self._formatter.writeln("")
