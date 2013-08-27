from .utils import TestCase
from .utils.test_generator import TestGenerator
from slash.loader import Loader
from slash.session import Session

from uuid import uuid1
import sys
import os

class TestRepositoryTest(TestCase):
    def setUp(self):
        super(TestRepositoryTest, self).setUp()
        self.generator = TestGenerator()
        self.package_name = "package_{0}".format(str(uuid1()).replace("-", "_"))
        self.root = self.generator.write_test_directory({
            self.package_name: {
                "__init__.py": "",
                "tests" : {
                    "__init__.py": "",
                    "dir1": {
                        "__init__.py": "",
                        "dir2": {
                            "__init__.py": "",
                            "test_1.py": self.generator.generate_test(),
                            "test_2.py": self.generator.generate_test(),
                        },
                    }}}}, self.get_new_path())

class ImportErrorsTest(TestRepositoryTest):
    def setUp(self):
        super(ImportErrorsTest, self).setUp()
        self.path = os.path.join(self.root, self.package_name, "tests", "dir1", "dir2")
        with open(os.path.join(self.path, "test_3.py"), "w") as f:
            f.write(":::")
        with open(os.path.join(self.path, "test_4.py"), "w") as f:
            f.write("import nonexistent_module_here")

    def test_import_errors_without_session(self):
        with self.assertRaises((SyntaxError, ImportError)):
            list(Loader().iter_path(self.root))

    def test_import_errors_with_session(self):
        with Session() as s:
            tests = list(Loader().iter_path(self.root))
        self.assertTrue(tests)
        self.assertFalse(s.result.global_result.is_success())
        errors = s.result.global_result.get_errors()
        self._assert_file_failed_with(errors, "test_3.py", SyntaxError)
        self._assert_file_failed_with(errors, "test_4.py", ImportError)

    def _assert_file_failed_with(self, errors, filename, error_type):
        [err] = [e for e in errors if e.exception_type is error_type]
        self.assertIn(filename, err.exception_text)

class PathLoadingTest(TestRepositoryTest):
    def test_iter_path(self):
        self.assert_all_discovered(Loader().iter_path(self.root))
    def test_iter_package_import_first(self):
        self._test_iter_package(True, False)
    def test_iter_package_import_first_force_init_py(self):
        self._test_iter_package(True, True)
    def test_iter_package_dont_import_first(self):
        self._test_iter_package(False, False)
    def _test_iter_package(self, import_first, force_init_py):
        sys.path.insert(0, self.root)
        package_name = "{0}.tests".format(self.package_name)
        if import_first:
            __import__(self.package_name)
            filename = sys.modules[self.package_name].__file__
            if force_init_py and not filename.endswith("__init__.py") and not filename.endswith("__init__.pyc"):
                sys.modules[self.package_name].__file__ = os.path.join(filename, "__init__.py")
        self.assert_all_discovered(Loader().iter_package(self.package_name))
        self.assertIn(self.package_name, sys.modules)
    def assert_all_discovered(self, iterator):
        tests = list(iterator)
        self.assertEquals(
            set(test.TESTGENERATOR_TEST_ID for test in tests),
            set(self.generator.get_expected_test_ids())
            )

