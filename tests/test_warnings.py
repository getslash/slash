from tempfile import mkdtemp
import functools, os, sys
import logbook
import slash
from io import StringIO
from .utils import TestCase
from .utils import run_tests_assert_success

_IDENTIFIER = "logging-test"
_SESSION_START_MARK = "session-start-mark"
_SESSION_END_MARK = "session-end-mark"
_WARNING_FILE_FORMAT = "WARNING: slash: {0}"
_WARNING_CONSOLE_FORMAT = "WARNING: {0}: {1}"
_DEBUG_FORMAT = "DEBUG: slash: {0}"

class WarningTest(TestCase):
    def test(self):
        self.log_path = mkdtemp()
        self.override_config(
            "log.root",
            self.log_path,
        )
        self.override_config(
            "log.subpath",
            os.path.join("{context.session.id}", "{context.test_id}", "debug.log")
        )
        self.override_config(
            "log.session_subpath",
            os.path.join("{context.session.id}", "debug.log")
        )

        self.saved_stderr = sys.stderr
        self.stderr = StringIO()
        sys.stderr = self.stderr

        self.override_config("log.console_level", 4) # for this test, we want to capture logs

        slash.hooks.session_start.register(functools.partial(_mark, _SESSION_START_MARK), identifier=_IDENTIFIER)
        self.addCleanup(slash.hooks.session_start.unregister_by_identifier, _IDENTIFIER)

        slash.hooks.session_end.register(functools.partial(_mark, _SESSION_END_MARK), identifier=_IDENTIFIER)
        self.addCleanup(slash.hooks.session_end.unregister_by_identifier, _IDENTIFIER)

        self.session = run_tests_assert_success(SampleTest)
        self.test_ids = [result.test_metadata.id for result in self.session.result.iter_test_results()]
        self._test_all_run()
        self._test_test_logs_written()
        self._test_session_logs()

        sys.stderr = self.saved_stderr

    def _test_all_run(self):
        methods = [
            method_name for method_name in dir(SampleTest)
            if method_name.startswith("test")
            ]
        self.assertTrue(methods)
        self.assertEquals(len(self.test_ids), len(methods))

    def _test_test_logs_written(self):
        for test_id in self.test_ids:
            log_path = os.path.join(self.log_path, self.session.id, test_id, "debug.log")
            with open(log_path) as f:
                data = f.read()
            self.assertIn(_DEBUG_FORMAT.format(test_id), data)
            self.assertIn(_WARNING_FILE_FORMAT.format(test_id), data)
            for other_test_id in self.test_ids:
                if other_test_id != test_id:
                    self.assertNotIn(other_test_id, data)
            self.assertNotIn(_SESSION_START_MARK, data)
            self.assertNotIn(_SESSION_END_MARK, data)

    def _test_session_logs(self):
        with open(os.path.join(self.log_path, self.session.id, "debug.log")) as f:
            data = f.read()
        self.assertIn(_WARNING_FILE_FORMAT.format(_SESSION_START_MARK), data)
        self.assertIn(_WARNING_FILE_FORMAT.format(_SESSION_END_MARK), data)
        for test_id in self.test_ids:
            self.assertNotIn(_DEBUG_FORMAT.format(test_id), data)
            self.assertNotIn(_WARNING_FILE_FORMAT.format(test_id), data)

        output = self.stderr.getvalue().strip()
        self.assertIn(_WARNING_CONSOLE_FORMAT.format(self.session.id, _SESSION_START_MARK), output)
        self.assertIn(_WARNING_CONSOLE_FORMAT.format(self.session.id, _SESSION_END_MARK), output)
        for test_id in self.test_ids:
            self.assertNotIn(_DEBUG_FORMAT.format(test_id), output)
            self.assertIn(_WARNING_CONSOLE_FORMAT.format(test_id, test_id), output)

class SampleTest(slash.Test):
    def test_1(self):
        _mark(level=logbook.DEBUG)
        _mark(level=logbook.WARNING)
    def test_2(self):
        _mark(level=logbook.DEBUG)
        _mark(level=logbook.WARNING)

def _mark(text=None, level=logbook.WARNING):
    if text is None:
        text = slash.context.test_id
    slash.logger.log(level, text)
