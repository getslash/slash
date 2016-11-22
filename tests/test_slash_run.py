from __future__ import print_function

import os
import sys

import pytest
from slash import config, site
from slash._compat import StringIO
from slash.frontend import slash_run
from slash.frontend.main import main_entry_point

from .utils import no_op, NullFile, TestCase


class SlashRunTestBase(TestCase):

    def setUp(self):
        super(SlashRunTestBase, self).setUp()
        self.override_config("run.session_state_path",
                             os.path.join(self.get_new_path(), "session_data"))


class MissingFilesTest(SlashRunTestBase):

    def test_slash_run_fails_fast_for_missing_files(self):
        result = slash_run.slash_run(
            ["/non/existing/path"], report_stream=NullFile())
        self.assertNotEquals(
            result, 0, "slash run unexpectedly succeeded for a missing path")


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

        self.forge.replace_with(
            slash_run, "_collect_tests", self._collect_tests_stub)
        self.forge.replace_with(
            sys, "argv", "/path/to/slash run -vv test1.py -x test2.py --pdb".split())
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

        self.assertTrue(self.stdout.getvalue().startswith(
            "usage: slash command..."), self.stdout.getvalue())


def test_slash_run_directory_success(suite):
    assert suite.run().exit_code == 0


def test_slash_run_default_directory(config_override, suite, suite_path):
    config_override("run.default_sources", [suite_path])
    suite.run(args=[], commit=False)


def test_slash_run_success_if_skips(suite):
    suite[1].when_run.skip()
    assert suite.run().exit_code == 0


def test_slash_run_from_file(tmpdir, suite):

    for i in range(20):
        suite.add_test()

    suite_path = suite.commit()

    assert len(suite.files) > 2
    file1 = suite.files[0]
    file2 = suite.files[-1]

    deselected = [t for t in suite if t.file not in (file1, file2)]
    assert deselected
    for d in deselected:
        d.expect_deselect()

    assert os.path.isdir(suite_path)

    filename1 = str(tmpdir.join("file1.txt"))
    filename2 = str(tmpdir.join("file2.txt"))

    for suite_file, filename in zip((file1, file2), (filename1, filename2)):
        with open(filename, "w") as f:
            print("# this is a comment", file=f)
            f_name = os.path.join(suite_path, suite_file.get_relative_path())
            assert os.path.isdir(suite_path)
            assert os.path.exists(f_name)
            print(f_name, file=f)

    suite.run(args=["-f", filename1, "-f", filename2], commit=False)


@pytest.mark.parametrize('failure_type', ['fail', 'error'])
def test_slash_run_directory_failure(suite, failure_type):
    getattr(suite[1].when_run, failure_type)()
    path = suite.commit()
    assert suite.run().exit_code != 0


def test_slash_run_specific_file(suite):

    for i in range(5):
        suite.add_test()
    suite_path = suite.commit()

    assert len(suite.files) > 1

    file = suite.files[1]

    deselected = [t for t in suite if t.file != file]
    assert deselected
    for t in deselected:
        t.expect_deselect()

    suite.run(args=[os.path.join(suite_path, file.get_relative_path())], commit=False)


@pytest.fixture(autouse=True)
def no_site_load(forge):
    forge.replace_with(site, 'load', no_op)


@pytest.fixture
def suite_path(suite):
    returned = suite.commit()
    assert os.path.isdir(returned)
    return returned
