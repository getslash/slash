import sys
import logbook
import slash
from slash import log
from slash._compat import cStringIO
from .utils import TestCase
from .utils.test_generator import TestGenerator
from slash.frontend import slash_run

class SlashRunTest(TestCase):
    def setUp(self):
        super(SlashRunTest, self).setUp()
        self.generator = TestGenerator()
        (self.success_test, self.fail_test,
         self.error_test, self.skip_test, self.warn_test) = self.generator.generate_tests(5)
        self.generator.make_test_skip(self.skip_test)
        self.generator.make_test_fail(self.fail_test)
        self.generator.make_test_raise_exception(self.error_test)
        self.generator.make_test_warn(self.warn_test)

        self.root_path = self.generator.write_test_directory(
            {
                "success_test.py" : self.success_test,
                "fail_test.py" : self.fail_test,
                "error_test.py" : self.error_test,
                "skip_test.py" : self.skip_test,
                "warn_test.py" : self.warn_test,
            }
        )
        self.report_stream = cStringIO()
        self.separator = "-" * 80
        slash.hooks.session_start.register(self._silence_console_logger, "silence_console")
        self.addCleanup(slash.hooks.session_start.unregister_by_identifier, "silence_console")

    def _silence_console_logger(self):
        slash.context.session.logging.console_handler.level = 1000000

    def _get_output_part(self, part):
        self.report_stream.seek(0)
        return self.report_stream.getvalue().split(self.separator)[part]
    def get_live_part(self):
        return self._get_output_part(0)
    def get_exceptions_part(self):
        return self._get_output_part(1)
    def get_summary_part(self):
        return self._get_output_part(2)
    def _slash_run(self):
        return slash_run.slash_run([self.root_path], report_stream=self.report_stream)
    def test_live_concise(self):
        self.override_config("log.console_level", logbook.WARNING)
        self._slash_run()
        result = self.get_live_part()
        self.assertEqual(set(result) - set("\n"), set("EFS."))
        self.assertEqual(len(result), 6)
    def test_live_verbose(self):
        self.override_config("log.console_level", logbook.INFO)
        self._slash_run()
        output = self.get_live_part()
        self._assert_reported(output, "error_test", "error\n Traceback")
        self._assert_reported(output, "fail_test", "fail\n Traceback")
        self._assert_reported(output, "skip_test", "skip\n Reason here")
        self._assert_reported(output, "success_test", "ok")

    def _assert_reported(self, output, test_name, additional_text):
        test = getattr(self, test_name)
        expected_output = "{0}.py:{1}.{2} ... {3}".format(
            test_name, test._test_class_name, 0, additional_text)
        if expected_output not in output:
            self.fail("Expected output {0!r} not found. Output was:\n{1}".format(expected_output, output))
    def test_summary(self):
        self._slash_run()
        output = self.get_summary_part()
        headers, values, empty_line, warning_header, warning = output.strip().splitlines()
        self.assertEqual(values.split(), ['2', '1', '1', '1'])
        self.assertEqual("", empty_line) # warn
        self.assertIn("Warnings:", warning_header) # warn
        self.assertIn("This is a warning", warning) # warn
    def test_exceptions_summary_verbose(self):
        self.override_config("log.console_level", logbook.INFO)
        self._slash_run()
        output = self.get_exceptions_part()
        self.assertEqual(output.count('>'), 3) # skip, error and fail
        self.assertEqual(output.count('Traceback'), 2) # error and fail
        self.assertIn("OSError: Sample exception", output) # error
        self.assertIn("TestFailed: Test failed", output) # fail
    def test_exceptions_summary_concise(self):
        self.override_config("log.console_level", logbook.WARNING)
        self._slash_run()
        output = self.get_exceptions_part()
        self.assertEqual(output.count('>'), 3) # skip, error and fail
        self.assertEqual(output.count('Traceback'), 0) # not tracebacks!
        self.assertIn("Sample exception", output) # error
        self.assertIn("Test failed", output) # fail
