from contextlib import contextmanager

from .function import CodeElement, Method
from .element import Element
from .method_test import MethodTest
from .test_container import SuiteWriterTestContainer


class Class(SuiteWriterTestContainer, CodeElement, Element):

    def __init__(self, suite, file):
        super(Class, self).__init__(suite)
        self._decorators = []
        self.file = file
        self.suite = file.suite
        self.name = 'Test{}'.format(self.id)
        self.before = self.after = None

    def add_before_method(self):
        assert self.before is None
        self.before = Method(self.suite, name='before')
        return self.before

    def add_after_method(self):
        assert self.after is None
        self.after = Method(self.suite, name='after')
        return self.after

    def add_decorator(self, decorator_string):
        self._decorators.append(decorator_string)

    def add_method_test(self):
        returned = MethodTest(self.suite, self)
        self._tests.append(returned)
        self.suite.notify_test_added(returned)
        return returned

    @contextmanager
    def _body_context(self, code_formatter):
        for d in self._decorators:
            code_formatter.write('@')
            code_formatter.writeln(d)
        code_formatter.writeln('class {}(slash.Test):'.format(self.name))
        with code_formatter.indented():

            if self.before is not None:
                self.before.write(code_formatter)
            if self.after is not None:
                self.after.write(code_formatter)

            yield

    def _write_body(self, code_formatter):
        super(Class, self)._write_body(code_formatter)
        for test in self._tests:
            test.write(code_formatter)
