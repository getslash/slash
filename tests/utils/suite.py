import itertools
import os
import sys
import shutil
from tempfile import mkdtemp
from uuid import uuid1

import slash
from slash._compat import itervalues

from .code_formatter import CodeFormatter

_SUCCESS = 'success'
_FAILURE = 'failure'
_ERROR = 'error'
_SKIP = 'skip'
_INTERRUPT = 'interrupt'

_SLASH_RESULTS_STORE_NAME = '__slash_suite_results__'


NUM_TESTS_PER_FILE = 5
NUM_TESTS_PER_CLASS = 2

_INDENT = " " * 4


def _uuid():
    return str(uuid1())


class TestSuite(object):

    def __init__(self, path=None):
        super(TestSuite, self).__init__()
        self.id_gen = itertools.count()
        self.files = []
        self._all_tests = []
        self._fixtures = []
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

    def add_test(self, regular_function=None, parent=None):
        if regular_function is None:
            regular_function = next(self._regular_function)
        test = PlannedTest(self, regular_function)
        if parent is None:
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

    def add_fixture(self, **kw):
        returned = Fixture(self, **kw)
        self._fixtures.append(returned)
        return returned

    def iter_fixtures(self):
        return iter(self._fixtures)

    def _get_test_container(self, regular_function):
        if not regular_function:
            return self._get_class_for_adding_test()

        return self._get_file_for_adding_test()

    def _get_class_for_adding_test(self):
        file = self._get_file_for_adding_test()
        if not file.classes or not file.classes[-1].can_add_test():
            cls = Class(self)
            cls.file = file
            file.classes.append(cls)
        return file.classes[-1]

    def _get_file_for_adding_test(self):
        if not self.files or not self.files[-1].can_add_test():
            self.files.append(File(self))
        return self.files[-1]

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

        if self._fixtures:
            with open(os.path.join(self._path, 'slashconf.py'), 'w') as f:
                formatter = CodeFormatter(f)

                formatter.writeln('import slash')

                for fixture in self._fixtures:
                    fixture.commit(formatter)
                    formatter.writeln()

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

    def run(self, stop_on_error=None, pattern=None, expect_interruption=False, reporter=None):
        if pattern is None:
            pattern = self._path
        self.commit()
        assert not _active_fixture_uuids
        with slash.Session(reporter=reporter) as session:
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
        verified_session = self.verify_last_run(stop_on_error=stop_on_error)
        assert session is verified_session.session
        assert not _active_fixture_uuids
        return verified_session

    def _get_test_ordinal(self, test):
        uuid = self._get_test_metadata_uuid(test.__slash__)
        return self._test_ordinal_by_uuid[uuid]

    def _get_test_metadata_uuid(self, test_metadata):
        if test_metadata.address_in_factory is not None and '.' in test_metadata.address_in_factory:
            # this is a method
            method_name = test_metadata.address_in_factory
            assert method_name.startswith(".test_")
            uuid = method_name[6:]
        else:
            function_name = test_metadata.factory_name
            assert function_name.startswith("test_")
            uuid = function_name[5:]

        if '(' in uuid:
            uuid = uuid[:uuid.index('(')]
        return uuid

    def verify_last_run(self, stop_on_error=False):
        import test
        saved_results = getattr(test, _SLASH_RESULTS_STORE_NAME, set())
        assert len(saved_results) == 1
        results = saved_results.pop()
        session = results.session
        return self._verify_results(session, stop_on_error=stop_on_error)

    def _verify_results(self, session, stop_on_error):
        if stop_on_error is None:
            stop_on_error = slash.config.root.run.stop_on_error
        returned = ResultWrapper(self, session)
        for result in session.results.iter_test_results():
            uuid = self._get_test_metadata_uuid(result.test_metadata)
            returned.results_by_test_uuid.setdefault(uuid, []).append(result)

        execution_stopped = False

        for test in self._all_tests:

            results = returned.results_by_test_uuid.get(test.uuid)

            if not test.selected:
                assert results is None or not any(r.is_started() for r in results), 'Deselected test {0} unexpectedly run!'.format(
                    test)
                continue

            assert results is not None, 'Result for {0} not found'.format(test)

            results = list(results)

            if execution_stopped:
                assert all(not r.is_started() for r in results)
                assert all(r.is_skip() for r in results)
                continue

            for param_variation, fixture_variation in itertools.product(
                    test.iter_parametrization_variations(),
                    test.iter_expected_fixture_variations()):
                for index, result in enumerate(results):
                    if param_variation == result.data.get('params') and fixture_variation == result.data.get('fixtures'):
                        test.verify_result(result)
                        if (result.is_error() or result.is_failure()) and stop_on_error:
                            execution_stopped = True

                        results.pop(index)
                        break
                else:
                    assert False, 'Result for params={0}, fixtures={1} of {2} not found!'.format(
                        param_variation, fixture_variation, test)

            assert not results, 'Unknown results found for {0}: {1}'.format(
                test, results)

        return returned

    def fail_in_middle(self):
        index = len(self) // 2
        assert index != 0 and index != len(self) - 1
        self[index].fail()
        return index

    def cleanup(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)


class SuiteObject(object):

    def __init__(self, suite):
        super(SuiteObject, self).__init__()
        self.suite = suite
        self.id = next(self.suite.id_gen)


class Class(SuiteObject):

    def __init__(self, suite):
        super(Class, self).__init__(suite)
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


class File(SuiteObject):

    def __init__(self, suite):
        super(File, self).__init__(suite)
        self.name = 'test_{0:05}.py'.format(self.id)
        self.path = self.name
        self.classes = []
        self.tests = []
        self._fixtures = []
        self._injected_lines = []

    def iter_fixtures(self):
        return iter(self._fixtures)

    def add_fixture(self, **kw):
        returned = Fixture(self.suite, file=self, **kw)
        self._fixtures.append(returned)
        return returned

    def inject_line(self, line):
        self._injected_lines.append(line)

    def can_add_test(self):
        return self.get_num_tests() < NUM_TESTS_PER_FILE

    def get_num_tests(self):
        return len(self.tests) + sum(len(cls.tests) for cls in self.classes)

    def commit(self, formatter):
        formatter.writeln('import slash')

        formatter.writeln('def _save_session_results():')
        formatter.writeln(
            '    "utility function to help debug results when tests are run indirectly"')
        formatter.writeln(
            '    import test  # best candidate to store results in an accessible place')
        formatter.writeln('    results = test.__dict__.setdefault("{0}", set())'.format(
            _SLASH_RESULTS_STORE_NAME))
        formatter.writeln('    if slash.session.results not in results:')
        formatter.writeln('        results.add(slash.session.results)')
        formatter.writeln()
        for line in self._injected_lines:
            formatter.writeln(line)

        formatter.writeln()

        for fixture in self._fixtures:
            fixture.commit(formatter)
            formatter.writeln()


class Parametrizable(object):

    def __init__(self):
        super(Parametrizable, self).__init__()
        self.params = {}

    def parametrize(self, num_params=3):
        param_name = 'param_{0:05}'.format(len(self.params))
        param_values = [_uuid() for i in range(num_params)]
        self.params[param_name] = param_values

    def iter_parametrization_variations(self):
        if not self.params:
            yield None
            return
        for combination in itertools.product(*itervalues(self.params)):
            yield dict(zip(self.params, combination))

    def add_parametrize_decorators(self, formatter):
        for param_name, values in self.params.items():
            formatter.writeln(
                '@slash.parametrize({0!r}, {1!r})'.format(param_name, values))


class Fixture(SuiteObject, Parametrizable):

    def __init__(self, suite, autouse=False, scope=None, file=None):
        super(Fixture, self).__init__(suite)
        self.file = file
        self.uuid = _uuid()
        self.name = 'fixture_{0:05}'.format(self.id)
        self.autouse = autouse
        self.scope=scope
        self.value = _uuid()
        self.fixtures = []
        self._cleanups = []

    def add_cleanup(self):
        returned = FixtureCleanup()
        self._cleanups.append(returned)
        return returned

    def verify_callbacks(self, result):
        expected = [evt.id for evt in self._cleanups[::-1]]
        if not expected:
            assert 'fixture_cleanups' not in result.data
        else:
            assert result.data['fixture_cleanups'] == expected

    def add_fixture(self, fixture):
        self.fixtures.append(fixture)

    def commit(self, formatter):
        dependent_names = list(self.params)
        dependent_names.extend(f.name for f in self.fixtures)

        arg_names = list(dependent_names)
        arg_names.insert(0, 'this')

        formatter.writeln('@slash.fixture{0}'.format(self._get_fixture_args_string()))
        self.add_parametrize_decorators(formatter)
        formatter.writeln(
            'def {0}({1}):'.format(self.name, ', '.join(arg_names)))
        with formatter.indented():
            formatter.writeln('_test_result = slash.context.result')

            fixture_info_dict_code = '{{ "value": {0!r}, "params": {{ {1} }} }}'.format(
                self.value, ', '.join('{0!r}: {0}'.format(name) for name in dependent_names))

            formatter.writeln('from {0} import _active_fixture_uuids'.format(__name__))
            formatter.writeln('assert {0!r} not in _active_fixture_uuids'.format(self.uuid))
            formatter.writeln('_active_fixture_uuids[{0!r}] = {1}'.format(self.uuid, fixture_info_dict_code))

            formatter.writeln('@this.add_cleanup')
            formatter.writeln('def _cleanup():')
            with formatter.indented():
                formatter.writeln('_active_fixture_uuids.pop({0!r})'.format(self.uuid))

            self._add_cleanup_code(formatter)

            formatter.writeln('return {0}'.format(fixture_info_dict_code))

    def _get_fixture_args_string(self):
        args = []
        if self.autouse:
            args.append('autouse=True')
        if self.scope is not None:
            args.append('scope={0!r}'.format(self.scope))
        return '' if not args else '({0})'.format(', '.join(args))

    def _add_cleanup_code(self, formatter):
        for index, cleanup in enumerate(self._cleanups):
            formatter.writeln('@this.add_cleanup')
            formatter.writeln('def callback{0}():'.format(index))
            with formatter.indented():
                formatter.writeln('_test_result.data.setdefault("fixture_cleanups", []).append({0!r})'.format(cleanup.id))
                formatter.writeln(cleanup.get_event_appending_line())



class PlannedTest(SuiteObject, Parametrizable):

    _expected_result = _SUCCESS

    def __init__(self, suite, regular_function):
        super(PlannedTest, self).__init__(suite)
        self.uuid = _uuid().replace("-", "_")
        self.regular_function = regular_function
        self.function_name = "test_{0}".format(self.uuid)
        self.selected = True
        self.cls = None
        self.file = None
        self._cleanups = []

        self._injected_lines = []
        self._fixtures = []
        self._decorators = []

    def iter_expected_fixture_variations(self):

        all_dependent_fixtures = list(self._get_all_dependent_fixtures())
        if not all_dependent_fixtures:
            yield None
            return

        value_spaces = []
        for f in all_dependent_fixtures:
            if not f.params:
                possible_params = [{}]
            else:
                possible_params = [dict(zip(f.params, combination))
                                   for combination in itertools.product(*itervalues(f.params))]
            value_spaces.append([{'value': f.value, 'params': params}
                                for params in possible_params])

        for combination in itertools.product(*value_spaces):
            fixture_dict = dict(zip(all_dependent_fixtures, combination))
            yield dict((fixture.name, self._build_fixture_variation(fixture, fixture_dict)) for fixture in self._fixtures)

    def _build_fixture_variation(self, fixture, fixture_dict):
        returned = {}
        returned['value'] = fixture_dict[fixture]['value']
        returned['params'] = fixture_dict[fixture]['params'].copy()
        for f in fixture.fixtures:
            returned['params'][f.name] = fixture_dict[f]

        return returned

    def _get_all_dependent_fixtures(self):
        returned = set()
        stack = []
        stack.extend(self._fixtures)
        while stack:
            f = stack.pop(-1)
            stack.extend(f.fixtures)
            returned.add(f)
        return returned

    def __repr__(self):
        return '<Planned test #{0.id}, selected={0.selected}, type={1}, expected result={0._expected_result}>'.format(
            self, 'function' if self.regular_function else 'method')

    def inject_line(self, stmt):
        self._injected_lines.append(stmt)

    def prepend_lines(self, lines):
        self._injected_lines = list(lines) + self._injected_lines

    def add_cleanup(self, critical=False):
        returned = Cleanup(critical=critical)
        self._cleanups.append(returned)
        self.prepend_lines([
            'def _cleanup():',
            '    slash.context.result.data.setdefault("cleanups", []).append({0!r})'.format(returned.id),
            '    {0}'.format(returned.get_event_appending_line()),
            'slash.add_{0}cleanup(_cleanup)'.format('critical_' if critical else '')])
        return returned

    def prepend_line(self, line):
        self.prepend_lines([line])

    def add_requirement(self, fullfilled, use_message=False):
        decorator = 'slash.requires(lambda : {0}'.format(bool(fullfilled))
        if use_message:
            decorator += ', message="some requirement message"'
        decorator += ')'
        self._decorators.append(decorator)
        if not fullfilled:
            self.expect_deselect()

    def add_fixture(self, fixture=None):
        if fixture is None:
            fixture = self.file.add_fixture()
        self._fixtures.append(fixture)
        return fixture

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

    def interrupt(self):
        self.inject_line('raise KeyboardInterrupt()')
        self.expect_interruption()

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
        self.add_parametrize_decorators(formatter)
        for decorator in self._decorators:
            formatter.writeln('@{0}'.format(decorator))
        formatter.writeln("def {0}({1}):".format(
            self.function_name, self._get_args_string()))
        with formatter.indented():
            formatter.writeln('_save_session_results()')
            for variable_name, variable_value in self._get_variables().items():
                formatter.writeln(
                    "{0} = {1!r}".format(variable_name, variable_value))
            for fixture in self._fixtures:
                formatter.writeln(
                    'slash.context.result.data.setdefault("fixtures", {{}})[{0!r}] = {0}'.format(fixture.name))
            for param_name in self.params:
                formatter.writeln(
                    'slash.context.result.data.setdefault("params", {{}})[{0!r}] = {0}'.format(param_name))
            assert sys.modules[__name__]._active_fixture_uuids is _active_fixture_uuids
            formatter.writeln('from {0} import _active_fixture_uuids'.format(__name__))
            formatter.writeln('slash.context.result.data["active_fixture_uuid_snapshot"] = frozenset(_active_fixture_uuids)')
            for returned in self._generate_test_statements():
                formatter.writeln(returned)
        formatter.writeln()

    def _get_args_string(self):
        args = []
        if self.cls is not None:
            args.append('self')

        for fixture in self._fixtures:
            args.append(fixture.name)

        args.extend(self.params)

        return ', '.join(args)

    def verify_result(self, result):

        for fixture in self._fixtures:
            fixture.verify_callbacks(result)

        for fixture in itertools.chain(self._fixtures, self.file.iter_fixtures(), self.suite.iter_fixtures()):
            if self._should_fixture_be_active(fixture):
                assert fixture.uuid in result.data['active_fixture_uuid_snapshot']

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
            if self._expected_result == _INTERRUPT and not cleanup.critical:
                assert cleanup.id not in result.data.get('cleanups', [])
            else:
                assert cleanup.id in result.data.get('cleanups', [])

    def _should_fixture_be_active(self, fixture):
        if fixture in self._fixtures:
            return True

        if not fixture.autouse:
            return False

        return fixture.file is self.file

    def _generate_test_statements(self):
        statements = self._injected_lines
        if not statements and not self._fixtures and not self.params:
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
        assert len(self.results_by_test_uuid[planned_test.uuid]
                   ) == 1, 'too many matching tests'
        return self.results_by_test_uuid[planned_test.uuid][0]

    def __contains__(self, x):
        try:
            self[x]
        except LookupError:
            return False
        return True


class Event(object):

    def __init__(self):
        super(Event, self).__init__()
        self.id = _uuid()

    def get_event_id(self):
        return '{0}:{1}'.format(type(self).__name__, self.id)

    def get_event_appending_line(self):
        return 'slash.context.result.data.setdefault("events", []).append({0!r})'.format(self.get_event_id())

class Cleanup(Event):

    def __init__(self, critical=False):
        super(Cleanup, self).__init__()
        self.critical = critical

class FixtureCleanup(Cleanup):
    pass

_active_fixture_uuids = {}
