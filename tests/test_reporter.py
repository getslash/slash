import logbook
from six.moves import cStringIO
from .utils import TestCase
from .utils.test_generator import TestGenerator
from shakedown.frontend import shake_run

class ShakeRunTest(TestCase):
    def setUp(self):
        super(ShakeRunTest, self).setUp()
        self.generator = TestGenerator()
        (self.success_test, self.fail_test,
         self.error_test, self.skip_test) = self.generator.generate_tests(4)
        self.generator.make_test_skip(self.skip_test)
        self.generator.make_test_fail(self.fail_test)
        self.generator.make_test_raise_exception(self.error_test)

        self.root_path = self.generator.write_test_directory(
            {
                "success_test.py" : self.success_test,
                "fail_test.py" : self.fail_test,
                "error_test.py" : self.error_test,
                "skip_test.py" : self.skip_test
            }
        )
        self.report_stream = cStringIO()
        self.separator = "-" * 80
    def _get_output_part(self, part):
        self.report_stream.seek(0)
        return self.report_stream.getvalue().split(self.separator)[part]
    def get_live_part(self):
        return self._get_output_part(0)
    def get_exceptions_part(self):
        return self._get_output_part(1)
    def get_summary_part(self):
        return self._get_output_part(2)
    def _shake_run(self):
        return shake_run.shake_run([self.root_path], report_stream=self.report_stream)
    def test_live_concise(self):
        self.override_config("log.console_level", logbook.WARNING)
        self._shake_run()
        result = self.get_live_part()
        self.assertEqual(set(result), set("EFS."))
        self.assertEqual(len(result), 4)
    def test_live_verbose(self):
        self.override_config("log.console_level", logbook.INFO)
        self._shake_run()
        output = self.get_live_part()
        self.assertIn('error_test.{0} ... error\n Traceback'.format(self.error_test._test_class_name), output)
        self.assertIn('fail_test.{0} ... fail\n Traceback'.format(self.fail_test._test_class_name), output)
        self.assertIn('skip_test.{0} ... skip\n Reason here'.format(self.skip_test._test_class_name), output)
        self.assertIn('success_test.{0} ... ok'.format(self.success_test._test_class_name), output)
    def test_summary(self):
        self._shake_run()
        output = self.get_summary_part()
        headers, values = output.strip().splitlines()
        self.assertEqual(values.split(), ['1'] * 4)
    def test_exceptions_summary_verbose(self):
        self.override_config("log.console_level", logbook.INFO)
        self._shake_run()
        output = self.get_exceptions_part()
        self.assertEqual(output.count('>'), 3) # skip, error and fail
        self.assertEqual(output.count('Traceback'), 2) # error and fail
        self.assertIn("OSError: Sample exception", output) # error
        self.assertIn("TestFailed: Test failed", output) # fail
    def test_exceptions_summary_concise(self):
        self.override_config("log.console_level", logbook.WARNING)
        self._shake_run()
        output = self.get_exceptions_part()
        self.assertEqual(output.count('>'), 3) # skip, error and fail
        self.assertEqual(output.count('Traceback'), 0) # not tracebacks!
        self.assertIn("Sample exception", output) # error
        self.assertIn("Test failed", output) # fail
        