import pytest
from .utils import TestCase
from .utils.test_generator import TestGenerator
from slash import Session
from slash.loader import Loader
from slash.exceptions import CannotLoadTests

from uuid import uuid1
import sys
import os


def test_import_error_registers_as_session_error(active_slash_session, test_loader):
    with pytest.raises(CannotLoadTests):
        test_loader.get_runnables(["/non/existent/path"])
    errors = active_slash_session.results.global_result.get_errors()
    assert len(errors) == 1
    [error] = errors


class TestRepositoryTest(TestCase):

    def setUp(self):
        super(TestRepositoryTest, self).setUp()
        self.generator = TestGenerator()
        self.package_name = "package_{0}".format(
            str(uuid1()).replace("-", "_"))
        self.root = self.generator.write_test_directory({
            self.package_name: {
                "__init__.py": "",
                "tests": {
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
        self.path = os.path.join(
            self.root, self.package_name, "tests", "dir1", "dir2")
        with open(os.path.join(self.path, "test_3.py"), "w") as f:
            f.write(":::")
        with open(os.path.join(self.path, "test_4.py"), "w") as f:
            f.write("import nonexistent_module_here")

    def test_import_errors_without_session(self):
        with self.assertRaises(CannotLoadTests):
            Loader().get_runnables(self.root)

    def test_import_errors_with_session(self):
        with Session() as s:
            tests = Loader().get_runnables(self.root)
        self.assertTrue(tests)
        self.assertFalse(s.results.global_result.is_success())
        errors = s.results.global_result.get_errors()
        self._assert_file_failed_with(errors, "test_3.py", "invalid syntax")
        self._assert_file_failed_with(
            errors, "test_4.py", ("No module named nonexistent", "No module named 'nonexistent"))

    def _assert_file_failed_with(self, errors, filename, message):
        if isinstance(message, str):
            messages = [message]
        else:
            messages = message
        [err] = [e for e in errors if any(m in e.message for m in messages)]
        self.assertIn(filename, err.message)


class PathLoadingTest(TestRepositoryTest):

    def test_get_runnables(self):
        self.assert_all_discovered(Loader().get_runnables(self.root))

    def assert_all_discovered(self, tests):
        assert isinstance(tests, list)
        self.assertEquals(
            set(test.TESTGENERATOR_TEST_ID for test in tests),
            set(self.generator.get_expected_test_ids())
        )


class PQNLoadingTest(TestCase):

    def setUp(self):
        super(PQNLoadingTest, self).setUp()
        self.root = self.get_new_path()
        self.classname_1 = "TestClass001"
        self.classname_2 = "TestClass002"

        with open(os.path.join(self.root, "file1.py"), "w") as f:
            f.write(
                _PARAMETERIZED_TEST_TEMPLATE.format(classname=self.classname_1))

        with open(os.path.join(self.root, "file2.py"), "w") as f:
            f.write(
                _PARAMETERIZED_TEST_TEMPLATE.format(classname=self.classname_1))

    def test_single_class(self):
        assert "@" not in _PARAMETERIZED_TEST_TEMPLATE, "Need to rewrite for parameters"
        num_tests = _PARAMETERIZED_TEST_TEMPLATE.count("def ")

        for pqn in ["file1.py:TestClass001", "file1.py"]:
            self._assert_loads(
                pqn, ["file1.py:TestClass001.test_method_1", "file1.py:TestClass001.test_method_2"])

    def test_one_pattern_not_found(self):
        ok_pattern = os.path.join(self.root, "file1.py:TestClass001")
        loader = Loader()
        unused = loader.get_runnables([ok_pattern])

        for pattern in [
                "file1.py:NonexistentTest",
                "file1.py:TestClass001.nonexistent_method",
                "file1.py:TestClass001(param=1)().test_method_1",
                "file1.py:TestClass001()(param=1).test_method_1",
                "file1.py:TestClass001()().test_method_1(param=1)",
        ]:
            pattern = os.path.join(self.root, pattern)

            with self.assertRaises(CannotLoadTests):
                Loader().get_runnables([ok_pattern, pattern])

    def _assert_loads(self, relative_pqn, expected_cases):
        pqn = os.path.join(self.root, relative_pqn)
        tests = Loader().get_runnables(pqn)
        expected_cases = [os.path.join(self.root, e) for e in expected_cases]
        self.assertEquals(set(str(test.__slash__.fqn)
                          for test in tests), set(expected_cases))

_PARAMETERIZED_TEST_TEMPLATE = """
import slash

class {classname}(slash.Test):

    def test_method_1(self):
        pass

    def test_method_2(self):
        pass
"""
