import itertools
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

        self._report_failures(session)
        self._report_errors(session)

        msg = "Session ended."
        kwargs = {"bold": True}
        if session.results.is_success():
            kwargs.update(green=True)
        else:
            kwargs.update(red=True)
            msg += " {0} failures, {1} errors.".format(session.results.get_num_failures(), session.results.get_num_errors())

        msg += " Total duration: {0}".format(self._format_duration(session.duration))
        self._terminal.sep("=", msg, **kwargs)  # pylint: disable=star-args

    def _report_failures(self, session):
        self._report_error_objects("FAILURES", session.results.iter_all_failures(), "F")

    def _report_errors(self, session):
        self._report_error_objects("ERRORS", session.results.iter_all_errors(), "E")

    def _report_error_objects(self, title, iterator, marker):
        self._terminal.sep("=", title)
        for result, errors in iterator:
            for error in errors:
                self._terminal.sep("_", str(result.test_metadata.fqn) if result.test_metadata else "**global**")
                self._report_error(error, marker)

    def _report_error(self, error, marker):
        line = ""
        frames = [] if not error.traceback else error.traceback.frames
        for index, frame in enumerate(frames):
            if index > 0:
                self._terminal.sep("- ")
            line = ""
            if frame.code_string:
                code_lines = frame.code_string.splitlines()
                line = ""
                for index, line in enumerate(code_lines):
                    if index == len(code_lines) - 1:
                        self._terminal.write(">", white=True, bold=True)
                    else:
                        self._terminal.write(" ")
                    self._terminal.write(line, white=True, bold=True)
                    self._terminal.write("\n")
            self._terminal.write("{0}:{1}:\n".format(frame.filename, frame.lineno))
        self._terminal.write(marker, red=True, bold=True)
        self._terminal.write("".join(itertools.takewhile(str.isspace, line)))
        self._terminal.write(error.message, red=True, bold=True)
        self._terminal.write("\n")

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

    def _format_duration(self, duration):
        seconds = duration % 60
        duration /= 60
        minutes = duration % 60
        hours = duration / 60
        return "{0:02}:{1:02}:{2:02}".format(int(hours), int(minutes), int(seconds))
