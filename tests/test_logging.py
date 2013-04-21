from .utils import TestCase
from .utils import run_tests_assert_success
from tempfile import mkdtemp
import functools
import os
import shakedown

_IDENTIFIER = "logging-test"
_SESSION_START_MARK = "session-start-mark"
_SESSION_END_MARK = "session-end-mark"

class LoggingTest(TestCase):
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

        shakedown.hooks.session_start.register(functools.partial(_mark, _SESSION_START_MARK), identifier=_IDENTIFIER)
        self.addCleanup(shakedown.hooks.session_start.unregister_by_identifier, _IDENTIFIER)

        shakedown.hooks.session_end.register(functools.partial(_mark, _SESSION_END_MARK), identifier=_IDENTIFIER)
        self.addCleanup(shakedown.hooks.session_end.unregister_by_identifier, _IDENTIFIER)

        self.session = run_tests_assert_success(SampleTest)
        self.test_ids = [result.test_metadata.id for result in self.session.iter_results()]
        self._test_all_run()
        self._test_test_logs_written()
        self._test_session_logs()

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

class SampleTest(shakedown.Test):
    def test_1(self):
        _mark()
    def test_2(self):
        _mark()

def _mark(text=None):
    if text is None:
        text = shakedown.context.test_id
    shakedown.logger.debug(text)
