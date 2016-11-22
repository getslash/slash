import os
from uuid import uuid4
import itertools
from contextlib import contextmanager

from .code_element import CodeElement
from .fixture import Fixture
from .generator_fixture import GeneratorFixture
from .nonmethod_test import NonMethodTest
from .test_class import Class
from .test_container import TestContainer


class File(TestContainer, CodeElement):

    def __init__(self, suite, relpath=None):
        super(File, self).__init__(suite)
        self._classes = []
        self._fixtures = []

        if relpath is None:
            relpath = 'test_{0}.py'.format(self.id)
        self._relpath = relpath

    @property
    def name(self):
        return os.path.basename(self._relpath)

    def add_hook_event(self, hook_name, extra_args=(), evt_name='evt'):
        self.append_line('@slash.hooks.{0}.register'.format(hook_name))
        event_code = '{0}_{1}'.format(evt_name, uuid4())
        self.append_line('def _hook():')
        self.append_line('    __ut__.events.add({0!r}, {1})'.format(
            event_code, ', '.join(extra_args)))
        return event_code

    @property
    def classes(self):
        return list(self._classes)

    def add_fixture(self, **kw):
        returned = Fixture(self.suite, self, **kw)
        self._fixtures.append(returned)
        return returned

    def add_generator_fixture(self):
        returned = GeneratorFixture(self.suite, self)
        self._fixtures.append(returned)
        return returned

    def get_relative_path(self):
        return self._relpath

    def add_class(self):
        cls = Class(self.suite, self)
        self._classes.append(cls)
        return cls

    def get_last_class(self):
        if not self._classes:
            return None
        return self._classes[-1]

    def add_function_test(self):
        returned = NonMethodTest(self.suite, self)
        self._tests.append(returned)
        self.suite.notify_test_added(returned)
        return returned

    @contextmanager
    def _body_context(self, code_formatter):
        with super(File, self)._body_context(code_formatter):
            if self.suite.debug_info:
                code_formatter.writeln('import __ut__')
            code_formatter.writeln('import slash')
            code_formatter.writeln()
            yield None

    def _write_body(self, code_formatter):
        super(File, self)._write_body(code_formatter)
        for thing in itertools.chain(self._classes, self._tests, self._fixtures):
            thing.write(code_formatter)
