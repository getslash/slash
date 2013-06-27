import colorama
import logbook
import itertools
from contextlib import contextmanager
from .formatter import Formatter
from .hooks_context_manager import HooksContextManager
from ..conf import config
from ..ctx import context

@contextmanager
def report_context(report_stream):
    is_concise = config.root.log.console_level > logbook.NOTICE
    live_reporter_type = ConciseLiveReporter if is_concise else VerboseLiveReporter
    with live_reporter_type(report_stream):
        yield
    if is_concise:
        report_stream.write("\n")
    SummaryReporter(report_stream).report_session(context.session)

def _format_unsuccessfull(formatter, result):
    with formatter.indented():
        for x in itertools.chain(result.get_failures(), result.get_errors(), result.get_skips()):
            formatter.writeln(x)

def _build_colorizer(fore_color_name):
    fore_color = getattr(colorama.Fore, fore_color_name.upper())
    return "{color}{{0}}{reset}".format(color=fore_color, reset=colorama.Fore.RESET).format  # pylint: disable=E1101

_REPORT_COLUMNS = [
    ("Successful", "get_num_successful", _build_colorizer("green")),
    ("Failures", "get_num_failures", _build_colorizer("red")),
    ("Errors", "get_num_errors", _build_colorizer("red")),
    ("Skipped", "get_num_skipped", _build_colorizer("yellow")),
    ]

class SummaryReporter(object):
    def __init__(self, stream):
        super(SummaryReporter, self).__init__()
        self._formatter = Formatter(stream)
        self._colorize = stream.isatty()
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

        summary = dict(
            (column_title, getattr(session.result, method_name)())
            for column_title, method_name, _ in _REPORT_COLUMNS
        )

        for is_header in (True, False):
            for column_title, _, colorizer in _REPORT_COLUMNS:
                count = summary[column_title]
                if is_header:
                    s = column_title
                else:
                    s = str(count)
                column_width = len(column_title) + 2
                if count and self._colorize:
                    colorized = colorizer(s)
                    column_width += len(colorized) - len(s)
                    s = colorized
                self._formatter.write(s.ljust(column_width))
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
