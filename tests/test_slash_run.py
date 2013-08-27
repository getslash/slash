from .utils import TestCase
from .utils import no_op
from .utils import NullFile
from .utils.test_generator import TestGenerator
from slash.frontend import slash_run
from slash import site
import os

class MissingFilesTest(TestCase):
    def test_slash_run_fails_fast_for_missing_files(self):
        result = slash_run.slash_run(["/non/existing/path"], report_stream=NullFile())
        self.assertNotEquals(result, 0, "slash run unexpectedly succeeded for a missing path")

class SlashRunTest(TestCase):
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
    def test_slash_run_directory_failure(self):
        self._test__slash_run_directory_unsuccessful(self.generator.make_test_fail)
    def test_slash_run_directory_error(self):
        self._test__slash_run_directory_unsuccessful(self.generator.make_test_raise_exception)
    def _test__slash_run_directory_unsuccessful(self, fault):
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
