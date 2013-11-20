from .utils import TestCase
from .utils import run_tests_assert_success, run_tests_in_session
import logbook
import functools
import os
import slash

_IDENTIFIER = "logging-test"
_SESSION_START_MARK = "session-start-mark"
_SESSION_END_MARK = "session-end-mark"

_silenced_logger = logbook.Logger("silenced_logger")

class LogFormattingTest(TestCase):

    def setUp(self):
        super(LogFormattingTest, self).setUp()
        self.log_path = self.get_new_path()
        self.override_config(
            "log.root", self.log_path
        )
        self.override_config(
            "log.format", "-- {record.message} --"
        )
        self.override_config("log.subpath", "debug.log")

    def test(self):
        self.session = run_tests_assert_success(SampleTest)
        with open(os.path.join(self.log_path, "debug.log")) as logfile:
            for line in logfile:
                self.assertTrue(line.startswith("-- "))
                self.assertTrue(line.endswith(" --\n"))

class LoggingTest(TestCase):
    def test(self):
        self.log_path = self.get_new_path()
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
        self.override_config(
            "log.silence_loggers",
            [_silenced_logger.name]
        )

        slash.hooks.session_start.register(functools.partial(_mark, _SESSION_START_MARK), identifier=_IDENTIFIER)
        self.addCleanup(slash.hooks.session_start.unregister_by_identifier, _IDENTIFIER)

        slash.hooks.session_end.register(functools.partial(_mark, _SESSION_END_MARK), identifier=_IDENTIFIER)
        self.addCleanup(slash.hooks.session_end.unregister_by_identifier, _IDENTIFIER)

        self.session = run_tests_assert_success(SampleTest)
        self.test_ids = [result.test_metadata.id for result in self.session.results.iter_test_results()]
        self._test_all_run()
        self._test_test_logs_written()
        self._test_session_logs()
        self._test_no_silenced_logger_records()

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
            for other_test_id in self.test_ids:
                if other_test_id != test_id:
                    self.assertNotIn(other_test_id, data)
            self.assertNotIn(_SESSION_START_MARK, data)
            self.assertNotIn(_SESSION_END_MARK, data)

    def _test_session_logs(self):
        with open(os.path.join(self.log_path, self.session.id, "debug.log")) as f:
            data = f.read()
        self.assertIn(_SESSION_START_MARK, data)
        self.assertIn(_SESSION_END_MARK, data)
        for test_id in self.test_ids:
            self.assertNotIn(test_id, data)

    def _test_no_silenced_logger_records(self):
        for path, _, filenames in os.walk(self.log_path):
            for filename in filenames:
                assert filename.endswith(".log")
                filename = os.path.join(path, filename)
                with open(filename) as f:
                    assert _silenced_logger.name not in f.read(), "Silenced logs appear in log file {0}".format(filename)

class ExtraLoggersTest(TestCase):

    def setUp(self):
        super(ExtraLoggersTest, self).setUp()
        self.session = slash.Session()
        self.handler = logbook.TestHandler()
        self.addCleanup(slash.log.remove_all_extra_handlers)
        slash.log.add_log_handler(self.handler)

    def test(self):
        run_tests_in_session(SampleTest, session=self.session)
        for test_result in self.session.results.iter_test_results():
            for record in self.handler.records:
                if test_result.test_id in record.message:
                    break
            else:
                self.fail("Test id {} does not appear in logger".format(test_result.test_id))

class SampleTest(slash.Test):
    def test_1(self):
        _mark()
    def test_2(self):
        _silenced_logger.error("error")
        _silenced_logger.info("info")
        _silenced_logger.debug("debug")
        _mark()

def _mark(text=None):
    if text is None:
        text = slash.context.test_id
    slash.logger.debug(text)

class TestLocaltimeLogging(TestCase):
    def setUp(self):
        super(TestLocaltimeLogging, self).setUp()
        self.assertFalse(slash.config.root.log.localtime)
        self.path = self.get_new_path()
        self.override_config(
            "log.localtime", True)
        self.override_config(
            "log.root", self.path)

    def test_local_time(self):
        with slash.Session() as s:
            slash.logger.info("Hello")
        self.assertNotEquals(os.listdir(self.path), [])
