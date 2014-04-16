import sys

import logbook
from py.io import TerminalWriter  # pylint: disable=import-error,no-name-in-module

from .reporter_interface import ReporterInterface


class ConsoleReporter(ReporterInterface):

    def __init__(self, level=logbook.DEBUG, stream=sys.stderr):
        super(ConsoleReporter, self).__init__()
        self._level = level
        self._stream = stream
        self._terminal = TerminalWriter(file=stream)

    def report_session_start(self, session):
        self._terminal.sep("=", "Session starts", white=True, bold=True)

    def report_session_end(self, session):
        kwargs = {"bold": True}
        if session.results.is_success():
            kwargs["green"] = True
        else:
            kwargs["red"] = True
        self._terminal.sep("=", "Session ended", **kwargs)

    def report_file_start(self, filename):
        self._file_failed = False
        self._file_has_skips = False
        self._terminal.write(filename)
        self._terminal.write(" ")

    def report_file_end(self, filename):
        self._terminal.write("  ")
        if self._file_failed:
            self._terminal.line("FAIL", red=True)
        elif self._file_has_skips:
            self._terminal.line("PASS", yellow=True)
        else:
            self._terminal.line("PASS", green=True)

    def report_test_success(self, test, result):
        self._terminal.write(".")

    def report_test_skip(self, test, result):
        self._terminal.write("s")
        self._file_has_skips = True

    def report_test_error(self, test, result):
        self._file_failed = True
        self._terminal.write("E")

    def report_test_failure(self, test, result):
        self._file_failed = True
        self._terminal.write("F")
