from __future__ import print_function

import os
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
        self.stderr = StringIO()
        self.stdout = StringIO()
        self.addCleanup(setattr, sys, "stderr", sys.stderr)
        self.forge.replace_with(sys, "stderr", self.stderr)
        self.addCleanup(setattr, sys, "stdout", sys.stdout)
        self.forge.replace_with(sys, "stdout", self.stdout)


    callback_success = False
    def _collect_tests_stub(self, app, args):
        self.assertTrue(config.root.debug.enabled)
        self.assertEquals(app.args.positionals, ["test1.py", "test2.py"])
        # this must be last to make sure the stub ran successfully
        self.callback_success = True
        return []

    def test_interspersed_positional_arguments(self):

        self.forge.replace_with(slash_run, "_collect_tests", self._collect_tests_stub)
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

class SlashHelpTest(ArgumentParsingTest):

    def _fake_execute(self, argv):
        prev_argv = list(sys.argv)
        sys.argv = argv[:]
        try:
            main_entry_point()
        finally:
            sys.argv = prev_argv

    def test_slash_run_help(self):

        with self.assertRaises(SystemExit):
            self._fake_execute(["slash", "run", "-h"])

        self.assertTrue(self.stdout.getvalue().startswith("usage: slash run "))
        self.assertIn("TEST [TEST ", self.stdout.getvalue())

    def test_slash_help(self):

        with self.assertRaises(SystemExit):
            self._fake_execute(["slash", "-h"])

        self.assertTrue(self.stdout.getvalue().startswith("usage: slash command..."), self.stdout.getvalue())


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

    def test_slash_run_from_file(self):
        filename1 = os.path.join(self.get_new_path(), "file1.txt")
        filename2 = os.path.join(self.get_new_path(), "file2.txt")
        with open(filename1, "w") as f:
            print("# this is a comment", file=f)
            print(os.path.join(self.root_path, "dir_1", "test_3.py"), file=f)

        with open(filename2, "w") as f:
            print("# this is a comment", file=f)
            print(os.path.join(self.root_path, "dir_1", "dir_2", "test_2.py"), file=f)


        result = self._execute_slash_run(["-f", filename1, "-f", filename2])
        self.assertEquals(result, 0, "usage: slash run failed")

        tests_run = self.generator.get_test_ids_run()
        self.assertEquals(len(tests_run), 3)

        # forget rest of tests
        self.generator.reset()

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

    def tearDown(self):
        self.generator.assert_all_run()
        super(SlashRunTest, self).tearDown()
