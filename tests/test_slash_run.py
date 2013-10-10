import sys
from .utils import TestCase
from .utils import no_op
from .utils import NullFile
from .utils.test_generator import TestGenerator
from slash.frontend import slash_run
from slash import config
from slash.frontend.main import main_entry_point
from slash._compat import StringIO
from slash import site
import os

class SlashRunTestBase(TestCase):
    def setUp(self):
        super(SlashRunTestBase, self).setUp()
        self.override_config("run.session_state_path", os.path.join(self.get_new_path(), "session_data"))


class MissingFilesTest(SlashRunTestBase):

    def test_slash_run_fails_fast_for_missing_files(self):
        result = slash_run.slash_run(["/non/existing/path"], report_stream=NullFile())
        self.assertNotEquals(result, 0, "slash run unexpectedly succeeded for a missing path")

class ArgumentParsingTest(TestCase):

    def setUp(self):
        super(ArgumentParsingTest, self).setUp()
        self.devnull = StringIO()
        self.forge.replace_with(sys, "stderr", self.devnull)

    callback_success = False
    def _test_iterator_stub(self, app, args):
        self.assertTrue(config.root.debug.enabled)
        self.assertEquals(app.args.remainder, ["test1.py", "test2.py"])
        # this must be last to make sure the stub ran successfully
        self.callback_success = True
        return ()

    def test_interspersed_positional_arguments(self):

        self.forge.replace_with(slash_run, "_get_test_iterator", self._test_iterator_stub)
        self.forge.replace_with(sys, "argv", "/path/to/slash run -vv test1.py -x test2.py --pdb".split())
        with self.assertRaises(SystemExit) as caught:
            main_entry_point()
        self.assertTrue(self.callback_success)
        if isinstance(caught.exception, int):
            # python 2.6
            code = caught.exception
        else:
            code = caught.exception.code
        self.assertEquals(code, 0)

class SlashRunTest(SlashRunTestBase):

    def setUp(self):
        super(SlashRunTest, self).setUp()
        self.generator = TestGenerator()
        make_test = self.generator.generate_test
        self.forge.replace_with(site, "load", no_op)
        self.root_path = self.generator.write_test_directory(
            {
                "test_1.py" : make_test(),
                "dir_1" : {
                    "dir_2" : {
                        "test_2.py" : [make_test(), make_test()],
                    },
                    "test_3.py" : make_test(),
                    "regular_file.txt" : "some content here",
                    "other_regular_file" : "more contents",
                }
            }, self.get_new_path()
        )

    def test_slash_run_directory_success(self):
        result = self._execute_slash_run([self.root_path])
        self.assertEquals(result, 0, "slash run did not return 0 on success")

    def test_slash_run_default_directory(self):
        self.override_config("run.default_sources", [self.root_path])
        self.assertEquals(self._execute_slash_run([]), 0)

    def test_slash_run_success_if_skips(self):
        self.generator.make_test_skip(self.generator.get_expected_test_ids()[1])
        result = self._execute_slash_run([self.root_path])
        self.assertEquals(result, 0, "skips cause nonzero return value")

    def test_slash_rerun(self):
        failing_test_id = self.generator.get_expected_test_ids()[1]
        self.generator.make_test_fail(failing_test_id)
        result = self._execute_slash_run([self.root_path])
        self.assertNotEquals(result, 0)

        self.generator.assert_all_run()

        self.generator.forget_run_test_ids()
        self.generator.make_test_fail(failing_test_id)
        result = self._execute_slash_rerun()
        self.assertNotEquals(result, 0)

        self.assertEquals(self.generator.get_test_ids_run(), [failing_test_id])

        self.generator.forget_run_test_ids()
        result = self._execute_slash_rerun()
        self.assertEquals(result, 0)

        self.assertEquals(self.generator.get_test_ids_run(), [failing_test_id])

        # tearDown will attempt to check assert_all_run...
        self.generator.reset()

    def test_slash_rerun_nonexistent_state_file(self):
        self.override_config("run.session_state_path", "/nonexisting_file")
        self.assertNotEquals(self._execute_slash_rerun(), 0)
        self.generator.reset() # don't complain over not run tests

    def test_slash_rerun_directory_state_file(self):
        self.override_config("run.session_state_path", self.get_new_path())
        self.assertNotEquals(self._execute_slash_rerun(), 0)
        self.generator.reset() # don't complain over not run tests

    def test_slash_rerun_skips(self):
        skipping_test_id = self.generator.get_expected_test_ids()[1]
        self.generator.make_test_skip(skipping_test_id)
        result = self._execute_slash_run([self.root_path])
        self.assertEquals(result, 0)
        self.generator.assert_all_run()

        self.generator.forget_run_test_ids()
        result = self._execute_slash_rerun()
        self.assertEquals(result, 0)
        self.assertEquals(self.generator.get_test_ids_run(), [])
        self.generator.reset() # tearDown will assert all tests were run

    def test_slash_run_directory_failure(self):
        self._test_slash_run_directory_unsuccessful(self.generator.make_test_fail)

    def test_slash_run_directory_error(self):
        self._test_slash_run_directory_unsuccessful(self.generator.make_test_raise_exception)

    def _test_slash_run_directory_unsuccessful(self, fault):
        expected = self.generator.get_expected_test_ids()
        fault(expected[2])
        result = self._execute_slash_run([self.root_path])
        self.assertNotEquals(result, 0, "slash run unexpectedly returned 0 for failure")

    def test_slash_run_specific_file(self):
        for path in [
                "test_1.py",
                "dir_1/dir_2/test_2.py",
                "dir_1/test_3.py"
        ]:
            result = self._execute_slash_run([os.path.join(self.root_path, path)])
            self.assertEquals(result, 0, "slash run did not return successfully for {0}".format(path))

    def _execute_slash_run(self, argv):
        return slash_run.slash_run(argv, report_stream=NullFile())

    def _execute_slash_rerun(self):
        return slash_run.slash_rerun([], report_stream=NullFile())

    def tearDown(self):
        self.generator.assert_all_run()
        super(SlashRunTest, self).tearDown()
