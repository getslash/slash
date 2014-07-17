import itertools
import os
import shutil
from tempfile import mkdtemp
from uuid import uuid1

import slash
from slash._compat import izip_longest

from .code_formatter import CodeFormatter

_SUCCESS = 'success'
_FAILURE = 'failure'
_ERROR = 'error'
_SKIP = 'skip'


NUM_CLASSES_PER_FILE = 3
NUM_TESTS_PER_CLASS = 3

_INDENT = " " * 4


class TestSuite(object):

    def __init__(self, path=None):
        super(TestSuite, self).__init__()
        self.id_gen = itertools.count()
        self.files = []
        self._all_tests = []
        if path is None:
            path = mkdtemp()
        self._path = path
        self._committed = False

    @property
    def path(self):
        return self._path

    def populate(self, num_tests=20):
        for i in range(num_tests):
            self.add_test()

    def add_test(self):
        test = PlannedTest(next(self.id_gen))
        cls = self._get_class_for_adding_test()
        assert test.cls is None
        test.cls = cls
        cls.tests.append(test)
        self._all_tests.append(test)
        return test

    def _get_class_for_adding_test(self):
        if self.files and not self.files[-1].classes[-1].can_add_test():
            return self.files[-1].classes[-1]
        new_class = Class(next(self.id_gen))
        assert new_class.file is None
        new_class.file = self._get_file_for_adding_class()
        new_class.file.classes.append(new_class)
        return new_class

    def _get_file_for_adding_class(self):
        if not self.files or not self.files[-1].can_add_class():
            self.files.append(File(next(self.id_gen)))
        return self.files[-1]

    @property
    def tests(self):
        for file in self.files:
            for cls in file.classes:
                for test in cls.tests:
                    yield test

    @property
    def classes(self):
        return [cls for file in self.files for cls in file.classes]

    def __len__(self):
        return len(self._all_tests)

    def __getitem__(self, idx):
        return self._all_tests[idx]

    def commit(self):
        if os.path.exists(self._path):
            shutil.rmtree(self._path)
        os.makedirs(self._path)
        for file in self.files:
            with open(os.path.join(self._path, file.name), 'w') as f:
                formatter = CodeFormatter(f)
                file.commit(formatter)
                for cls in file.classes:
                    cls.commit(formatter)
        return self._path

    def fix_all(self):
        for test in self._all_tests:
            test.fix()

    def run(self, stop_on_error=None, pattern=None):
        if pattern is None:
            pattern = self._path
        self.commit()
        with slash.Session() as session:
            with session.get_started_context():
                self.session_id = session.id
                slash.runner.run_tests(
                    slash.loader.Loader().get_runnables([pattern], sort_key=lambda test: test.__slash__.address), stop_on_error=stop_on_error)
        return self._verify_results(session, stop_on_error=stop_on_error)

    def _verify_results(self, session, stop_on_error):
        returned = ResultWrapper(self, session)
        for result in session.results.iter_test_results():
            method_name = result.test_metadata.address_in_factory
            assert method_name.startswith(".test_")
            uuid = method_name[6:]
            returned.results_by_test_uuid[uuid] = result

        should_skip = False

        for test in self._all_tests:
            result = returned.results_by_test_uuid.get(test.uuid)
            if not test.selected:
                assert result is None, 'Deselected test {0} unexpectedly run!'.format(
                    test)
                continue
            assert result is not None, 'Result for {0} not found'.format(test)
            if should_skip:
                assert not result.is_started()
                assert result.is_skip()
            else:
                test.verify_result(result)

            if (result.is_error() or result.is_failure()) and stop_on_error:
                should_skip = True
        return returned

    def fail_in_middle(self):
        index = len(self) // 2
        assert index != 0 and index != len(self) - 1
        self[index].fail()
        return index

    def cleanup(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)


class Class(object):

    def __init__(self, id):
        super(Class, self).__init__()
        self.id = id
        self.name = "Test{0:05}".format(self.id)
        self.tests = []
        self.file = None
        self._decorators = []

    def decorate(self, decorator):
        assert not decorator.startswith('@')
        self._decorators.insert(0, decorator)

    def can_add_test(self):
        return len(self.tests) < NUM_TESTS_PER_CLASS

    def commit(self, formatter):
        for decorator in self._decorators:
            formatter.writeln('@{0}'.format(decorator))
        formatter.writeln("class {0}(slash.Test):".format(self.name))
        with formatter.indented():
            for test in self.tests:
                test.commit(formatter)


class File(object):

    def __init__(self, id):
        super(File, self).__init__()
        self.id = id
        self.name = 'test_{0:05}.py'.format(self.id)
        self.classes = []
        self._injected_lines = []

    def inject_line(self, line):
        self._injected_lines.append(line)

    def can_add_class(self):
        return len(self.classes) < NUM_CLASSES_PER_FILE

    def commit(self, formatter):
        formatter.writeln('import slash')

        for line in self._injected_lines:
            formatter.writeln(line)


class PlannedTest(object):

    _expected_result = _SUCCESS

    def __init__(self, id):
        super(PlannedTest, self).__init__()
        self.id = id
        self.uuid = str(uuid1()).replace("-", "_")
        self.method_name = "test_{0}".format(self.uuid)
        self.selected = True
        self.cls = None

        self._injected_statements = []

    def __repr__(self):
        return '<Planned test #{0.id}, selected={0.selected}, expected result={0._expected_result}>'.format(self)

    def inject_statement(self, stmt):
        self._injected_statements.append(stmt)

    def rename(self, new_name):
        self.method_name = new_name

    def is_success(self):
        return self.status == _SUCCESS

    def expect_deselect(self):
        self.selected = False

    def fail(self):
        self.inject_statement('assert 1 == 2')
        self.expect_failure()

    def expect_failure(self):
        self._expected_result = _FAILURE

    def error(self):
        self.inject_statement('object.unknown_attribute()')
        self.expect_error()

    def expect_error(self):
        self._expected_result = _ERROR

    def skip(self):
        self.inject_statement('from slash import skip_test')
        self.inject_statement('skip_test("reason")')
        self.expect_skip()

    def expect_skip(self):
        self._expected_result = _SKIP

    def fix(self):
        del self._injected_statements[:]
        self._expected_result = _SUCCESS

    def commit(self, formatter):
        formatter.writeln("def {0}(self):".format(self.method_name))
        with formatter.indented():
            for variable_name, variable_value in self._get_variables().items():
                formatter.writeln(
                    "{0} = {1!r}".format(variable_name, variable_value))
            for s in self._generate_test_statements():
                formatter.writeln(s)

    def verify_result(self, result):
        if self._expected_result == _SUCCESS:
            assert result.is_success()
        elif self._expected_result == _FAILURE:
            assert result.is_failure()
            assert not result.is_error()
        elif self._expected_result == _ERROR:
            assert result.is_error()
            assert not result.is_failure()
        elif self._expected_result == _SKIP:
            assert not result.is_error()
            assert not result.is_failure()
            assert result.is_skip()
        else:
            raise NotImplementedError()  # pragma: no cover

    def _generate_test_statements(self):
        statements = self._injected_statements
        if not statements:
            statements = ['pass']

        for statement in statements:
            yield statement

    def _get_variables(self):
        return {}


class ResultWrapper(object):

    def __init__(self, suite, session):
        super(ResultWrapper, self).__init__()
        self.suite = suite
        self.session = session

        self.results_by_test_uuid = {}

    def __getitem__(self, planned_test):
        return self.results_by_test_uuid[planned_test.uuid]
