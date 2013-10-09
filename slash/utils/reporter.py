import logbook
import itertools
from contextlib import contextmanager
from .formatter import Formatter
from .color_string import ColorString
from .hooks_context_manager import HooksContextManager
from .._compat import string_types
from ..conf import config
from ..ctx import context

def _is_concise():
    return config.root.log.console_level > logbook.NOTICE

@contextmanager
def report_context(report_stream):
    live_reporter_type = ConciseLiveReporter if _is_concise() else VerboseLiveReporter
    with live_reporter_type(report_stream):
        yield
    if _is_concise():
        report_stream.write("\n")
    SummaryReporter(report_stream).report_session(context.session)

def _format_unsuccessful(formatter, result):
    console_level = config.root.log.console_level
    with formatter.indented():
        for exc_obj in itertools.chain(result.get_failures(), result.get_errors(), result.get_skips()):
            if isinstance(exc_obj, string_types) or console_level > logbook.NOTICE:
                formatter.writeln(exc_obj)
            elif console_level > logbook.INFO:
                formatter.writeln("({0.exception!r})".format(exc_obj))
            else:
                formatter.writeln(exc_obj.exception_text)

_YELLOW = ColorString.get_formatter("yellow")
_RED = ColorString.get_formatter("red")
_GREEN = ColorString.get_formatter("green")

_REPORT_COLUMNS = [
    ("Successful", "get_num_successful", _GREEN),
    ("Failures", "get_num_failures", _RED),
    ("Errors", "get_num_errors", _RED),
    ("Skipped", "get_num_skipped", _YELLOW),
    ]

class SummaryReporter(object):
    def __init__(self, stream):
        super(SummaryReporter, self).__init__()
        self._formatter = Formatter(stream)
    def report_session(self, session):
        self._describe_unsuccessful(session)
        self._describe_summary(session)
        self._describe_warnings(session)
    def _describe_unsuccessful(self, session):
        self._formatter.write_separator()
        for result in session.results.iter_all_results():
            if result.is_success():
                continue
            self._formatter.write("> ")
            if result.is_skip():
                self._formatter.write(_YELLOW("SKIP"))
            elif result.is_error():
                self._formatter.write(_RED("ERROR"))
            elif result.is_failure():
                self._formatter.write(_RED("FAILURE"))
            else:
                raise NotImplementedError() # pragma: no cover
            if result.test_metadata is None:
                self._formatter.write(" (Outside tests)")
            else:
                self._formatter.write(" ", result.test_metadata)
            _format_unsuccessful(self._formatter, result)

    def _describe_summary(self, session):
        self._formatter.write_separator()

        summary = dict(
            (column_title, getattr(session.results, method_name)())
            for column_title, method_name, _ in _REPORT_COLUMNS
        )


        for is_header in (True, False):
            for column_title, _, colorizer in _REPORT_COLUMNS:
                column_width = len(column_title) + 2

                count = summary[column_title]
                if is_header:
                    s = column_title.ljust(column_width)
                else:
                    s = str(count)

                if count:
                    orig = s
                    s = colorizer(s)
                    column_width += len(s) - len(orig)
                self._formatter.write(s.ljust(column_width))
            self._formatter.writeln()

    def _describe_warnings(self, session):
        if session.warnings:
            self._formatter.writeln()
            self._formatter.writeln("Warnings:")
            for record in session.warnings:
                self._formatter.writeln(record)

class BaseLiveReporter(HooksContextManager):
    def __init__(self, report_stream):
        super(BaseLiveReporter, self).__init__()
        self._formatter = Formatter(report_stream)

class VerboseLiveReporter(BaseLiveReporter):
    def on_test_start(self):
        self._formatter.write("> ", context.test)
        self._formatter.writeln(" ...")
    def on_test_success(self):
        self._formatter.writeln("ok")
    def on_test_error(self):
        self._formatter.writeln("error")
    def on_test_failure(self):
        self._formatter.writeln("fail")
    def on_test_skip(self, reason): # pylint: disable=W0613
        self._formatter.writeln("skip")

class ConciseLiveReporter(BaseLiveReporter):
    def on_test_success(self):
        self._formatter.write(".")
    def on_test_error(self):
        self._formatter.write("E")
    def on_test_failure(self):
        self._formatter.write("F")
    def on_test_skip(self, reason): # pylint: disable=W0613
        self._formatter.write("S")
    def on_result_summary(self):
        self._formatter.writeln("")
