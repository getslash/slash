from contextlib import contextmanager

from .function import CodeElement
from .element import Element
from .method_test import MethodTest
from .test_container import TestContainer


class Class(TestContainer, CodeElement, Element):

    def __init__(self, suite, file):
        super(Class, self).__init__(suite)
        self._decorators = []
        self.file = file
        self.suite = file.suite
        self.name = 'Test{0}'.format(self.id)

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
        code_formatter.writeln('class {0}(slash.Test):'.format(self.name))
        with code_formatter.indented():
            yield

    def _write_body(self, code_formatter):
        super(Class, self)._write_body(code_formatter)
        for test in self._tests:
            test.write(code_formatter)
