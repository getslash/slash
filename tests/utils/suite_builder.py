import os
from uuid import uuid4

from slash._compat import izip_longest
from slash.frontend.slash_run import slash_run

from .suite_writer.utils import get_code_lines

class SuiteBuilder(object):

    def __init__(self, path):
        super(SuiteBuilder, self).__init__()
        self.path = path
        self.files = [SuiteBuilderFile()]

    def build(self):
        returned = SuiteBuilderSuite(os.path.join(self.path, 'suite-{}'.format(uuid4())))
        for index, file in enumerate(self.files):
            with open(os.path.join(returned.path, 'test_file_{}.py'.format(index)), 'w') as f:
                for code in file.code_snippets:
                    for line in get_code_lines(code):
                        f.write(line)
                        f.write('\n')
        return returned

    @property
    def first_file(self):
        return self.files[0]


class SuiteBuilderFile(object):

    def __init__(self):
        self.code_snippets = []

    def add_code(self, code):
        self.code_snippets.append(code)
        return self


class SuiteBuilderSuite(object):

    def __init__(self, path):
        self.path = path
        os.makedirs(path)

    def run(self):
        app = slash_run([self.path])
        return SuiteBuilderSuiteResult(app)


class SuiteBuilderSuiteResult(object):

    def __init__(self, slash_app):
        self.slash_app = slash_app

    def assert_success(self, num_tests):
        return self.assert_all(num_tests).success()

    def assert_all(self, num_tests):
        assert len(self.slash_app.session.results) == num_tests
        return AssertAllHelper(self)

    def assert_results(self, num_results):
        results = list(self.slash_app.session.results.iter_test_results())
        assert len(results) == num_results
        return results

    def assert_session_error(self, error_substring):
        self.assert_all(0)
        errs = self.slash_app.session.results.global_result.get_errors()
        assert len(errs) == 1
        assert error_substring in str(errs[0])

    def with_data(self, data_sets):
        results = list(self.slash_app.session.results)
        data_sets = list(data_sets)
        while data_sets:
            data_set = data_sets.pop()
            for index, result in enumerate(results):
                if result.data == data_set:
                    results.pop(index)
                    break
            else:
                assert False, 'No result found for {}'.format(data_set)
        assert not results
        return self

class AssertAllHelper(object):

    def __init__(self, suite_builder_result):
        self.suite_builder_result = suite_builder_result
        self._results = suite_builder_result.slash_app.session.results

    def success(self):
        assert self._results.is_success(allow_skips=False)
        return self.suite_builder_result

    def errors(self, errors_list):
        for res, error in izip_longest(self._results, errors_list):
            errs = res.get_errors()
            assert len(errs) == 1
            assert errs[0] == error
        return self.suite_builder_result
