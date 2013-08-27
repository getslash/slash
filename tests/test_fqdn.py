"""
Test the usage of FQDNs in Slash, to uniquely identify tests being run.
"""
import itertools
import os

import slash
from .utils import TestCase
from .utils import run_tests_assert_success

class FQDNTestBase(TestCase):

    def setUp(self):
        super(FQDNTestBase, self).setUp()
        self.root = self.get_new_path()
        self.filename = os.path.join(self.root, "testfile.py")
        with open(self.filename, "w") as f:
            f.write(_TEST_FILE_TEMPLATE)

        self.session = run_tests_assert_success(slash.loader.Loader().iter_path(self.filename))
        self.results = list(self.session.result.iter_test_results())

class FQDNTest(FQDNTestBase):

    def test_simple_test_fqdn(self):
        simple_test_fqdn = self.results[0].test_metadata.fqdn
        self.assertEquals(str(simple_test_fqdn), "{0}:TestClass.test_method".format(self.filename))

    def test_parameterized_test_fqdn(self):
        parameterized = set(str(x.test_metadata.fqdn) for x in self.results[1:])

        self.assertEquals(parameterized, set(
            "{0}:ParameterizedTestClass(a={1})(c={2}).test_parameters(b={3})".format(self.filename, a, c, b)
            for a, b, c in itertools.product([1, 2], [3, 4], [5, 6])))

class FQDNFromPycFilesTest(FQDNTestBase):

    def setUp(self):
        super(FQDNFromPycFilesTest, self).setUp()
        self.new_filename = self.filename + "c"
        assert self.new_filename.endswith(".pyc")
        self.fqdn = self.results[0].test_metadata.fqdn

    def test_pyc_files_original_exists(self):
        "Filenames ending with .pyc should be normalized to .py"
        self.fqdn.set_path(self.new_filename)
        self.assertEquals(self.fqdn.get_path(), self.filename)

    def test_pyc_files_original_missing(self):
        "When the original python file is missing and the filename ends with .pyc, it should not be fixed"
        os.unlink(self.filename)
        self.fqdn.set_path(self.new_filename)
        self.assertEquals(self.fqdn.get_path(), self.new_filename)


_TEST_FILE_TEMPLATE = """
import slash

class TestClass(slash.Test):
    def test_method(self):
        pass

class ParameterizedTestClass(slash.Test):

    @slash.parameters.iterate(a=[1, 2])
    def before(self, a):
        pass

    @slash.parameters.iterate(b=[3, 4])
    def test_parameters(self, b):
        pass

    @slash.parameters.iterate(c=[5, 6])
    def after(self, c):
        pass
"""
