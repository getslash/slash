# pylint: disable=import-error,no-name-in-module
import collections
import itertools
import sys

from py.io import TerminalWriter

from .._compat import iteritems
from ..log import VERBOSITIES
from ..utils.iteration import iteration
from ..utils.python import wraps
from .reporter_interface import ReporterInterface


def from_verbosity(level):
    def decorator(func):
        @wraps(func)
        def new_func(self, *args, **kwargs):
            if self._verobsity_allows(level):  # pylint: disable=protected-access
                return func(self, *args, **kwargs)

        return new_func
    return decorator

class TerminalWriterWrapper(object):

    def __init__(self, file):
        super(TerminalWriterWrapper, self).__init__()
        self._writer = TerminalWriter(file=file)
        self._line = ""

    def sep(self, *args, **kw):
        self._line = ""
        return self._writer.sep(*args, **kw)

    def write(self, line, **kw):
        line = str(line)
        self._writer.write(line, **kw)
        if "\n" in line:
            line = line.rsplit("\n", 1)[-1].rsplit("\r", 1)[-1]
            self._line = line
        else:
            self._line += line

    def line(self, *args, **kw):
        self._writer.line(*args, **kw)
        self._line = ""

    def get_line_in_progress(self):
        return self._line

    def clear_line_in_progress(self):
        if self._line and self._writer.hasmarkup:
            self._writer.write("\r")
            self._writer.write(" " * len(self._line))
            self._writer.write("\r")

    def restore_line_in_progress(self):
        if self._writer.hasmarkup:
            self._writer.write(self._line)


class ConsoleReporter(ReporterInterface):

    def __init__(self, level, stream=sys.stderr):
        super(ConsoleReporter, self).__init__()
        self._level = level
        self._stream = stream
        self._terminal = TerminalWriterWrapper(file=stream)

    def notify_before_console_output(self):
        self._terminal.clear_line_in_progress()

    def notify_after_console_output(self):
        self._terminal.restore_line_in_progress()

    def report_collection_start(self):
        self._report_num_collected([], stillworking=True)

    def report_test_collected(self, all_tests, test):
        self._report_num_collected(all_tests, stillworking=True)

    def report_collection_end(self, collected):
        self._report_num_collected(collected, stillworking=False)

    def _report_num_collected(self, collected, stillworking):
        self._terminal.write("\r{0} tests collected{1}".format(len(collected), "..." if stillworking else "   \n"), white=True, bold=True)

    def _is_verbose(self, level):
        return self._level <= level

    @from_verbosity(VERBOSITIES.ERROR)
    def report_session_start(self, session):
        self._terminal.sep("=", "Session starts".format(self._level), white=True, bold=True)

    def report_session_end(self, session):

        if not self._verobsity_allows(VERBOSITIES.WARNING):
            self._terminal.write("\n")  # for concise outputs we need to break the sequence of dots...

        if self._verobsity_allows(VERBOSITIES.ERROR):
            self._report_failures(session)
            self._report_errors(session)
        elif self._verobsity_allows(VERBOSITIES.CRITICAL):
            self._report_failures_and_errors_concise(session)

        if self._verobsity_allows(VERBOSITIES.INFO):
            self._report_all_skips(session)

        if self._verobsity_allows(VERBOSITIES.WARNING):
            self._report_warning_summary(session)

        kwargs = {"bold": True}
        msg = "Session ended."
        if session.results.is_success():
            kwargs.update(green=True)
        else:
            kwargs.update(red=True)
            msg += " {0} successful, {1} skipped, {2} failures, {3} errors.".format(
                session.results.get_num_successful(), session.results.get_num_skipped(),
                session.results.get_num_failures(), session.results.get_num_errors())

        msg += " Total duration: {0}".format(self._format_duration(session.duration))
        self._terminal.sep("=", msg, **kwargs)  # pylint: disable=star-args

    def _report_warning_summary(self, session):
        warnings_by_key = collections.defaultdict(list)
        for warning in session.warnings:
            warnings_by_key[warning.key].append(warning)
        for i, (warning_key, warnings) in iteration(iteritems(warnings_by_key)):
            if i.first:
                self._terminal.sep("=", "Warnings ({0} total)".format(len(session.warnings)), yellow=True)
            self._terminal.write(
                " * {d[filename]}:{d[lineno]:03} -- ".format(d=warnings[0].details), yellow=True)
            self._terminal.write(warnings[0].details['message'], yellow=True, bold=True)
            self._terminal.write(
                " (Repeated {0} times)\n".format(len(warnings)), yellow=True)

    def _verobsity_allows(self, level):
        return self._level <= level

    def _report_failures(self, session):
        self._report_error_objects("FAILURES", session.results.iter_all_failures(), "F")

    def _report_errors(self, session):
        self._report_error_objects("ERRORS", session.results.iter_all_errors(), "E")

    def _report_error_objects(self, title, iterator, marker):
        iterator = list(iterator)
        total_num_errors = sum(len(errors) for _, errors in iterator)
        error_number = 0
        for result_iteration, (result, errors) in iteration(iterator):
            if result_iteration.first:
                self._terminal.sep("=", title)

            for error_iteration, error in iteration(errors):
                error_number += 1
                self._report_error_location(result, error_number, total_num_errors, marker, error)
                self._report_error(result, error, marker)

    def _report_error_location(self, result, object_index, total_num_errors, marker, error):
        self._terminal.sep("_", '{0}: {1}'.format(error.time, self._get_location(result)))
        if self._verobsity_allows(VERBOSITIES.INFO) and result.test_metadata:
            location = "{3}:{0}{1}/{2}".format(
                marker, object_index, total_num_errors, result.test_metadata.id)
            self._terminal.sep("_", location)

    def _report_failures_and_errors_concise(self, session):
        for result in session.results.iter_all_results():
            if result.get_errors() or result.get_failures():
                self._terminal.write(self._get_location(result))
                self._terminal.write(":")
                if result.get_errors():
                    self._terminal.write(" {0} errors".format(len(result.get_errors())))
                if result.get_failures():
                    self._terminal.write(" {0} failures".format(len(result.get_failures())))
                self._terminal.write("\n")

    def _get_location(self, result):
        return str(result.test_metadata.fqn) if result.test_metadata else "**global**"

    def _report_error(self, result, error, marker):
        line = ""
        if not error.traceback:
            frames = []
        elif self._level > VERBOSITIES.WARNING:
            frames = [error.traceback.frames[-1]]
        else:
            frames = error.traceback.frames
        for frame_iteration, frame in iteration(frames):
            if not frame_iteration.first:
                self._terminal.sep("- ")
            self._write_frame_locals(frame)
            code_lines = self._write_frame_code(frame)
            if frame_iteration.last:
                self._terminal.write(marker, red=True, bold=True)
                if code_lines:
                    indent = "".join(itertools.takewhile(str.isspace, code_lines[-1]))
                else:
                    indent = ""
                self._terminal.write(self._indent_with(error.message, indent), red=True, bold=True)
                self._terminal.write("\n")
            self._terminal.write("{0}:{1}:\n".format(frame.filename, frame.lineno))

        log_path = result.get_log_path()
        if log_path is not None:
            self._terminal.write("(Log file: {0})\n".format(log_path), black=True, bold=True)


    def _indent_with(self, text, indent):
        return "\n".join(indent + line for line in text.splitlines())

    def _report_all_skips(self, session):
        for item, result in iteration(result for result in session.results.iter_test_results() if result.is_skip()):
            if item.first:
                self._terminal.sep("=", "SKIPS")
            self._terminal.write(result.test_metadata, yellow=True)
            self._terminal.write("\t")
            self._terminal.write(result.get_skips()[0])
            self._terminal.write("\n")

    @from_verbosity(VERBOSITIES.NOTICE)
    def _write_frame_locals(self, frame):
        if not frame.locals and not frame.globals:
            return
        for index, (name, value) in enumerate(itertools.chain(iteritems(frame.locals), iteritems(frame.globals))):
            if index > 0:
                self._terminal.write(", ")
            self._terminal.write("{0}: ".format(name), yellow=True, bold=True)
            self._terminal.write(value["value"])
        self._terminal.write("\n\n")

    def _write_frame_code(self, frame):
        if frame.code_string:
            if self._verobsity_allows(VERBOSITIES.NOTICE):
                code_lines = frame.code_string.splitlines()
            else:
                code_lines = [frame.code_line]
            line = ""
            for line_iteration, line in iteration(code_lines):
                if line_iteration.last:
                    self._terminal.write(">", white=True, bold=True)
                else:
                    self._terminal.write(" ")
                self._terminal.write(line, white=True, bold=True)
                self._terminal.write("\n")
            return code_lines


    @from_verbosity(VERBOSITIES.WARNING)
    def report_file_start(self, filename):
        self._file_failed = False
        self._file_has_skips = False
        self._terminal.write(filename)
        self._terminal.write(" ")

    @from_verbosity(VERBOSITIES.WARNING)
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
        self._terminal.write("s", yellow=True)
        self._file_has_skips = True

    def report_test_error(self, test, result):
        self._file_failed = True
        self._terminal.write("E", red=True)

    def report_test_failure(self, test, result):
        self._file_failed = True
        self._terminal.write("F", red=True)

    def _format_duration(self, duration):
        seconds = duration % 60
        duration /= 60
        minutes = duration % 60
        hours = duration / 60
        return "{0:02}:{1:02}:{2:02}".format(int(hours), int(minutes), int(seconds))
