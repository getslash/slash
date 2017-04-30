from .utils import TestCase
from .utils import run_tests_assert_success
import itertools
import os
import slash
from slash._compat import izip_longest
import pytest

from .utils.suite_writer import Suite


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
            raise NotImplementedError()  # pragma: no cover


@pytest.mark.parametrize('parametrize', [True, False])
def test_function_name(suite, suite_test, parametrize):
    if parametrize:
        suite_test.add_parameter(num_values=3)

    summary = suite.run()
    for result in summary.get_all_results_for_test(suite_test):
        function_name = result.test_metadata.function_name
        assert function_name.startswith('test_')
        assert '.' not in result.test_metadata.function_name
        assert '(' not in result.test_metadata.function_name


def test_variation(suite, suite_test):
    fixture = suite.slashconf.add_fixture()
    param = fixture.add_parameter()  # pylint: disable=unused-variable
    suite_test.depend_on_fixture(fixture)
    suite_test.append_line('slash.context.result.data["variation"] = slash.context.test.__slash__.variation.values.copy()')
    summary = suite.run()
    for result in summary.get_all_results_for_test(suite_test):
        assert len(result.data['variation']) == 1
        assert fixture.name not in result.data['variation']
        assert '{}.{}'.format(fixture.name, param.name) in result.data['variation']


def test_function_name_with_special_parameters(test_type):
    suite = Suite()
    assert len(suite) == 0  # pylint: disable=len-as-condition
    suite_test = suite.add_test(type=test_type)
    values = ['a.b', 'a(b']
    suite_test.add_parameter(values=values)

    # we can't verify result because we would not be able to parse the function properly
    # TODO: this will change once we properly support variations metadata  # pylint: disable=fixme
    summary = suite.run(verify=False, sort=False)
    for result, value in izip_longest(summary.session.results, values):
        function_name = result.test_metadata.function_name
        assert value not in function_name
        assert '.' not in result.test_metadata.function_name
        assert '(' not in result.test_metadata.function_name
        assert function_name.startswith('test_')


def test_module_name_not_none_or_empty_string(suite):
    for result in suite.run().session.results:
        assert result.test_metadata.module_name


def test_test_index(suite):
    index = None
    session = suite.run().session
    for index, result in enumerate(session.results):
        assert result.test_metadata.test_index0 == index
        assert result.test_metadata.test_index1 == index + 1
    assert index > 0


def test_set_test_name(suite, suite_test):
    result = suite.run()[suite_test]
    metadata = result.test_metadata
    assert metadata.file_path in str(metadata)
    custom_name = 'some_custom_name'
    metadata.set_test_full_name(custom_name)
    assert str(metadata) == '<{0}>'.format(custom_name)


def test_class_name_with_dot_parameters():

    # pylint: disable=unused-argument

    @slash.parametrize('path', ['x.y'])
    def test_something(path):
        pass

    with slash.Session() as s:  # pylint: disable=unused-variable
        loader = slash.loader.Loader()
        [test] = loader.get_runnables(test_something)  # pylint: disable=unbalanced-tuple-unpacking
        assert test.__slash__.class_name is None


class TestMetadataTest(TestCase):
    loaded_tests = []

    def setUp(self):
        @slash.hooks.register
        def tests_loaded(tests): # pylint: disable=unused-variable
            TestMetadataTest.loaded_tests = tests

        super(TestMetadataTest, self).setUp()
        self.root = self.get_new_path()
        self.filename = os.path.join(self.root, "testfile.py")
        with open(self.filename, "w") as f:
            f.write(_TEST_FILE_TEMPLATE)

        with slash.Session() as s:
            self.session = run_tests_assert_success(self.filename, session=s)
            self.tests = self.loaded_tests
        self.results = list(self.session.results.iter_test_results())
        self.results.sort(key=lambda result: str(result.test_metadata))

    def test_tests_have_correct_metadata(self):
        for test, result in zip(self.tests, self.session.results.iter_test_results()):
            self.assertIs(test.__slash__, result.test_metadata)

    def test_simple_test_address(self):
        self.assertEqual(self.results[0].test_metadata.address, "{0}:T001.test_method".format(self.filename))

    def test_parameterized_test_address(self):
        parameterized = set(x.test_metadata.address for x in self.results[1:])

        self.assertEqual(parameterized, set(
            "{0}:T002.test_parameters(after:c={2},b={3},before:a={1})".format(self.filename, a, c, b)
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
