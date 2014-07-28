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
_INTERRUPT = 'interrupt'


NUM_TESTS_PER_FILE = 5
NUM_TESTS_PER_CLASS = 2

_INDENT = " " * 4


class TestSuite(object):

    def __init__(self, path=None):
        super(TestSuite, self).__init__()
        self.id_gen = itertools.count()
        self.files = []
        self._all_tests = []
        self._test_ordinal_by_uuid = {}
        if path is None:
            path = mkdtemp()
        self._path = path
        self._committed = False
        self._regular_function = itertools.cycle([True, False])

    @property
    def path(self):
        return self._path

    def populate(self, num_tests=20):
        for i in range(num_tests):
            self.add_test()

    def add_test(self, regular_function=None):
        if regular_function is None:
            regular_function = next(self._regular_function)
        test = PlannedTest(next(self.id_gen), regular_function)
        parent = self._get_test_container(regular_function)
        if not regular_function:
            assert test.cls is None
            test.cls = parent
            test.file = parent.file
        else:
            test.file = parent
        parent.tests.append(test)
        self._test_ordinal_by_uuid[test.uuid] = len(self._all_tests)
        self._all_tests.append(test)
        return test

    def _get_test_container(self, regular_function):
        if not regular_function:
            return self._get_class_for_adding_test()

        return self._get_file_for_adding_test()


    def _get_class_for_adding_test(self):
        file = self._get_file_for_adding_test()
        if not file.classes or not file.classes[-1].can_add_test():
            cls = Class(next(self.id_gen))
            cls.file = file
            file.classes.append(cls)
        return file.classes[-1]

    def _get_file_for_adding_test(self):
        if not self.files or not self.files[-1].can_add_test():
            self.files.append(File(next(self.id_gen)))
        return self.files[-1]

    @property
    def tests(self):
        for file in self.files:
            for test in file.tests:
                yield test
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
                for test in file.tests:
                    test.commit(formatter)
                for cls in file.classes:
                    cls.commit(formatter)
        return self._path

    def fix_all(self):
        for test in self._all_tests:
            test.fix()

    def run(self, stop_on_error=None, pattern=None, expect_interruption=False):
        if pattern is None:
            pattern = self._path
        self.commit()
        with slash.Session() as session:
            with session.get_started_context():
                self.session_id = session.id
                try:
                    slash.runner.run_tests(
                        slash.loader.Loader().get_runnables([pattern], sort_key=self._get_test_ordinal), stop_on_error=stop_on_error)
                except KeyboardInterrupt:
                    if not expect_interruption:
                        raise
                else:
                    assert not expect_interruption, 'Test run did not get interrupted'
                slash.hooks.result_summary()
        return self._verify_results(session, stop_on_error=stop_on_error)

    def _get_test_ordinal(self, test):
        uuid = self._get_test_metadata_uuid(test.__slash__)
        return self._test_ordinal_by_uuid[uuid]

    def _get_test_metadata_uuid(self, test_metadata):
        if test_metadata.address_in_factory is None:
            function_name = test_metadata.factory_name
            assert function_name.startswith("test_")
            uuid = function_name[5:]
        else:
            method_name = test_metadata.address_in_factory
            assert method_name.startswith(".test_")
            uuid = method_name[6:]
        return uuid

    def _verify_results(self, session, stop_on_error):
        if stop_on_error is None:
            stop_on_error = slash.config.root.run.stop_on_error
        returned = ResultWrapper(self, session)
        for result in session.results.iter_test_results():
            uuid = self._get_test_metadata_uuid(result.test_metadata)
            returned.results_by_test_uuid[uuid] = result

        execution_stopped = False

        for test in self._all_tests:
            result = returned.results_by_test_uuid.get(test.uuid)
            if not test.selected:
                assert result is None, 'Deselected test {0} unexpectedly run!'.format(
                    test)
                continue
            assert result is not None, 'Result for {0} not found'.format(test)
            if execution_stopped:
                assert not result.is_started()
                assert result.is_skip()
            else:
                test.verify_result(result)

            if (result.is_error() or result.is_failure()) and stop_on_error:
                execution_stopped = True
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
        self.path = self.name
        self.classes = []
        self.tests = []
        self._injected_lines = []

    def inject_line(self, line):
        self._injected_lines.append(line)

    def can_add_test(self):
        return self.get_num_tests() < NUM_TESTS_PER_FILE

    def get_num_tests(self):
        return len(self.tests) + sum(len(cls.tests) for cls in self.classes)

    def commit(self, formatter):
        formatter.writeln('import slash')

        for line in self._injected_lines:
            formatter.writeln(line)


class PlannedTest(object):

    _expected_result = _SUCCESS

    def __init__(self, id, regular_function):
        super(PlannedTest, self).__init__()
        self.id = id
        self.uuid = str(uuid1()).replace("-", "_")
        self.regular_function = regular_function
        self.function_name = "test_{0}".format(self.uuid)
        self.selected = True
        self.cls = None
        self.file = None
        self._cleanups = []

        self._injected_lines = []

    def __repr__(self):
        return '<Planned test #{0.id}, selected={0.selected}, type={1}, expected result={0._expected_result}>'.format(
            self, 'function' if self.regular_function else 'method')

    def inject_line(self, stmt):
        self._injected_lines.append(stmt)

    def prepend_lines(self, lines):
        self._injected_lines = list(lines) + self._injected_lines

    def add_cleanup(self, critical=False):
        cleanup_id = str(uuid1())
        self._cleanups.append({'id': cleanup_id, 'critical': critical})
        self.prepend_lines([
            'def _cleanup():',
            '    slash.context.result.data.setdefault("cleanups", []).append({0!r})'.format(cleanup_id),
            'slash.add_{0}cleanup(_cleanup)'.format('critical_' if critical else '')])

    def prepend_line(self, line):
        self.prepend_lines([line])

    def rename(self, new_name):
        self.function_name = new_name

    def is_success(self):
        return self.status == _SUCCESS

    def expect_deselect(self):
        self.selected = False

    def fail(self):
        self.inject_line('assert 1 == 2')
        self.expect_failure()

    def expect_failure(self):
        self._expected_result = _FAILURE

    def expect_interruption(self):
        self._expected_result = _INTERRUPT

    def error(self):
        self.inject_line('object.unknown_attribute()')
        self.expect_error()

    def expect_error(self):
        self._expected_result = _ERROR

    def skip(self):
        self.inject_line('from slash import skip_test')
        self.inject_line('skip_test("reason")')
        self.expect_skip()

    def expect_skip(self):
        self._expected_result = _SKIP

    def fix(self):
        del self._injected_lines[:]
        self._expected_result = _SUCCESS

    def commit(self, formatter):
        formatter.writeln("def {0}({1}):".format(self.function_name, 'self' if not self.regular_function else ''))
        with formatter.indented():
            for variable_name, variable_value in self._get_variables().items():
                formatter.writeln(
                    "{0} = {1!r}".format(variable_name, variable_value))
            for s in self._generate_test_statements():
                formatter.writeln(s)
        formatter.writeln()

    def verify_result(self, result):
        if self._expected_result == _SUCCESS:
            assert result.is_success()
        elif self._expected_result == _FAILURE:
            assert result.is_failure()
            assert not result.is_error()
        elif self._expected_result == _ERROR:
            assert result.is_error()
            assert not result.is_failure()
            assert not result.is_success()
            assert not result.is_skip()
        elif self._expected_result == _SKIP:
            assert result.is_skip()
            assert not result.is_error()
            assert not result.is_failure()
            assert not result.is_success()
        elif self._expected_result == _INTERRUPT:
            assert result.is_interrupted()
            assert not result.is_error()
            assert not result.is_failure()
            assert not result.is_success()
        else:
            raise NotImplementedError()  # pragma: no cover

        for cleanup in self._cleanups:
            if self._expected_result == _INTERRUPT and not cleanup['critical']:
                assert cleanup['id'] not in result.data.get('cleanups', [])
            else:
                assert cleanup['id'] in result.data.get('cleanups', [])

    def _generate_test_statements(self):
        statements = self._injected_lines
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
