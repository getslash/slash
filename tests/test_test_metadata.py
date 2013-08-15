from .utils import TestCase
from .utils.test_generator import TestGenerator
import os
import shutil
import slash
import tempfile


class TestMetadataTest(TestCase):

    def setUp(self):
        super(TestMetadataTest, self).setUp()
        self.generator = TestGenerator()
        self.test_promise = self.generator.generate_test()
        self.root = os.path.abspath(os.path.realpath(self.generator.write_test_directory({
            "pkg": {
                "__init__.py": "",
                "test_1.py": self.test_promise,
            }})))
        self.addCleanup(shutil.rmtree, self.root)
        self.addCleanup(os.chdir, os.path.abspath("."))
        os.chdir(self.root)
        with slash.Session() as s:
            self.session = s
            [self.test] = tests = list(slash.loader.Loader().iter_path(self.root))
            slash.run_tests(tests)
        [self.result] = self.session.result.iter_test_results()
        self.test_case = self.test_promise.get_test_case()

    def test_test_metadata(self):
        self.assertIs(self.test_case.__slash__, self.result.test_metadata)
        self.assertEquals(self.test_case.__slash__.fqdn.get_abspath(), os.path.abspath(os.path.join(self.root, "pkg", "test_1.py")))
        self.assertEquals(self.test_case.__slash__.fqdn.get_path(), os.path.join("pkg", "test_1.py"))
