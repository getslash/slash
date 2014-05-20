import itertools
import os
import shutil
from tempfile import mkdtemp

import slash
from slash._compat import izip_longest

_SUCCESS, _FAILURE, _ERROR, _SKIP = (1 << x for x in range(4))


NUM_CLASSES_PER_FILE = 3
NUM_TESTS_PER_CLASS = 3

_INDENT = " " * 4


class TestSuite(object):

    def __init__(self, num_tests=20):
        super(TestSuite, self).__init__()
        self.tests = [PlannedTest(i) for i in range(num_tests)]
        self._path = mkdtemp()
        self._committed = False

    def __len__(self):
        return len(self.tests)

    def __getitem__(self, idx):
        return self.tests[idx]

    def commit(self):
        shutil.rmtree(self._path)
        os.makedirs(self._path)
        for test in self.tests:
            test.commit(self._path)
        pass

    def fix_all(self):
        for test in self.tests:
            test.fix()

    def run(self, stop_on_error=None):
        self.commit()
        with slash.Session() as session:
            self.session_id = session.id
            slash.runner.run_tests(
                slash.loader.Loader().get_runnables([self._path], sort_key=lambda test: test.__slash__.fqn.address_in_module.method_name), stop_on_error=stop_on_error)
        return self._verify_results(session, stop_on_error=stop_on_error)

    def _verify_results(self, session, stop_on_error):
        results = list(session.results.iter_test_results())
        results.sort(key=lambda result: result.test_metadata.fqn.address_in_module.method_name)
        should_be_run = True
        for result, test in izip_longest(results, self.tests):
            if should_be_run:
                test.verify_result(result)
            else:
                assert not result.is_started()
                assert result.is_skip()
            if result.is_error() or result.is_failure() and stop_on_error:
                should_be_run = False
        return session.results

    def fail_in_middle(self):
        index = len(self.tests) // 2
        assert index != 0 and index != len(self.tests) - 1
        self.tests[index].fail()
        return index

    def cleanup(self):
        pass

class PlannedTest(object):

    result = _SUCCESS

    def __init__(self, id):
        super(PlannedTest, self).__init__()
        self.id = id
        self.method_name = "test_{0:04}".format(self.id)

    def fail(self):
        self.result = _FAILURE

    def fix(self):
        if self.result != _SKIP:
            self.result = _SUCCESS

    def commit(self, parent_path):
        with open(os.path.join(parent_path, "test_{0:04}.py".format(self.id // NUM_CLASSES_PER_FILE)), "a") as f:
            if self.id % NUM_CLASSES_PER_FILE == 0:
                f.write("from slash import Test, should\n\n")

            if self.id % NUM_TESTS_PER_CLASS == 0:
                test_class_name = "Test{0:04}".format(self.id // NUM_TESTS_PER_CLASS)
                f.write("class {0}(Test):\n".format(test_class_name))
            f.write(_INDENT)
            f.write("def {0}(self):\n".format(self.method_name))
            for variable_name, variable_value in self._get_variables().items():
                f.write(_INDENT * 2)
                f.write("{0} = {1!r}\n".format(variable_name, variable_value))
            f.write(_INDENT * 2)
            f.write(self._generate_test_statement())
            f.write("\n\n")

    def verify_result(self, result):
        if self.result == _SUCCESS:
            assert result.is_success()
        elif self.result == _FAILURE:
            assert result.is_failure()
            assert not result.is_error()
        elif self.result == _ERROR:
            assert result.is_error()
            assert not result.is_failure()
        else:
            raise NotImplementedError() # pragma: no cover

    def _generate_test_statement(self):
        if self.result == _SUCCESS:
            return "pass"
        elif self.result == _FAILURE:
            return "should.equal(1, 2)"
        elif self.result == _ERROR:
            return "x = unknown"
        else:
            raise NotImplementedError() # pragma: no cover

    def _get_variables(self):
        return {}
