from .utils import TestCase
from .utils import run_tests_assert_success
from .utils.test_generator import TestGenerator
import itertools
import os
import shutil
import slash
import tempfile

class TestMetadataTest(TestCase):

    def setUp(self):
        super(TestMetadataTest, self).setUp()
        self.root = self.get_new_path()
        self.filename = os.path.join(self.root, "testfile.py")
        with open(self.filename, "w") as f:
            f.write(_TEST_FILE_TEMPLATE)

        self.tests = slash.loader.Loader().get_runnables(self.filename)
        self.session = run_tests_assert_success(self.tests)
        self.results = list(self.session.results.iter_test_results())
        self.results.sort(key = lambda result: str(result.test_metadata.fqn))

    def test_tests_have_correct_metadata(self):
        for test, result in zip(self.tests, self.session.results.iter_test_results()):
            self.assertIs(test.__slash__, result.test_metadata)

    def test_simple_test_fqn(self):
        simple_test_fqn = self.results[0].test_metadata.fqn
        self.assertEquals(simple_test_fqn, "{0}:T001.test_method".format(self.filename))

    def test_parameterized_test_fqn(self):
        parameterized = set(str(x.test_metadata.fqn) for x in self.results[1:])

        self.assertEquals(parameterized, set(
            "{0}:T002(a={1})(c={2}).test_parameters(b={3})".format(self.filename, a, c, b)
            for a, b, c in itertools.product([1, 2], [3, 4], [5, 6])))

_TEST_FILE_TEMPLATE = """
import slash

class T001(slash.Test):
    def test_method(self):
        pass

class T002(slash.Test):

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
