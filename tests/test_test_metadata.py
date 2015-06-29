from .utils import TestCase
from .utils import run_tests_assert_success
import itertools
import os
import slash
import pytest


@pytest.mark.parametrize('parametrize', [True, False])
def test_class_name(suite, suite_test, test_type, parametrize):
    if parametrize:
        suite_test.add_parameter(num_values=3)
    summary = suite.run()
    for result in summary.get_all_results_for_test(suite_test):
        if test_type == 'method':
            assert result.test_metadata.class_name.startswith('Test')
            assert '(' not in result.test_metadata.class_name
        elif test_type == 'function':
            assert result.test_metadata.class_name is None
        else:
            raise NotImplementedError() # pragma: no cover


@pytest.mark.parametrize('parametrize', [True, False])
def test_function_name(suite, suite_test, test_type, parametrize):
    if parametrize:
        suite_test.add_parameter(num_values=3)

    summary = suite.run()
    for result in summary.get_all_results_for_test(suite_test):
        function_name = result.test_metadata.function_name
        assert function_name.startswith('test_')
        assert '.' not in result.test_metadata.function_name
        assert '(' not in result.test_metadata.function_name


def test_module_name_not_none_or_empty_string(suite):
    for result in suite.run().session.results:
        assert result.test_metadata.module_name


def test_test_index(suite):
    session = suite.run().session
    for index, result in enumerate(session.results):
        assert result.test_metadata.test_index0 == index
        assert result.test_metadata.test_index1 == index + 1


class TestMetadataTest(TestCase):

    def setUp(self):
        super(TestMetadataTest, self).setUp()
        self.root = self.get_new_path()
        self.filename = os.path.join(self.root, "testfile.py")
        with open(self.filename, "w") as f:
            f.write(_TEST_FILE_TEMPLATE)

        with slash.Session() as s:
            self.tests = slash.loader.Loader().get_runnables(self.filename)
            self.session = run_tests_assert_success(self.tests, session=s)
        self.results = list(self.session.results.iter_test_results())
        self.results.sort(key=lambda result: str(result.test_metadata))

    def test_tests_have_correct_metadata(self):
        for test, result in zip(self.tests, self.session.results.iter_test_results()):
            self.assertIs(test.__slash__, result.test_metadata)

    def test_simple_test_address(self):
        self.assertEquals(self.results[0].test_metadata.address, "{0}:T001.test_method".format(self.filename))

    def test_parameterized_test_address(self):
        parameterized = set(x.test_metadata.address for x in self.results[1:])

        self.assertEquals(parameterized, set(
            "{0}:T002.test_parameters(before:a={1}, after:c={2}, b={3})".format(self.filename, a, c, b)
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
