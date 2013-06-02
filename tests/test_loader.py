from .utils import TestCase
from .utils.test_generator import TestGenerator
from shakedown.loader import Loader

from uuid import uuid1
import shutil
import sys

class PathLoadingTest(TestCase):
    def setUp(self):
        super(PathLoadingTest, self).setUp()
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
                    }
                }
            }
        })
        self.addCleanup(shutil.rmtree, self.root)
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
