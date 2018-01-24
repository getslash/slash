import os
from uuid import uuid4

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
        assert len(self.slash_app.session.results) == num_tests
        assert self.slash_app.session.results.is_success(allow_skips=False)
        return self

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
