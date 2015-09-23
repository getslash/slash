import py.code

from slash._compat import StringIO
from .element import Element
from ..code_formatter import CodeFormatter

from contextlib import contextmanager


class CodeElement(Element):

    def __init__(self, suite):
        super(CodeElement, self).__init__(suite)
        self.suite = suite
        self._body = []

    def append_line(self, line):
        self._body.append(line)

    def prepend_line(self, line):
        self._body.insert(0, line)

    def write(self, code_formatter):
        with self._body_context(code_formatter):
            self._write_body(code_formatter)

    def append_body(self, code_element):
        """An easier way to write multiline injected code:

        @code_element.append_body
        def __code__():
            some_code_line()
            for i in range(20):
                some_other_code()
        """
        source_lines = str(py.code.Code(code_element).source()).splitlines()
        assert source_lines[0].startswith('@')
        assert source_lines[1].startswith('def ')
        assert source_lines[2][0].isspace()
        for line in str(py.code.Source('\n'.join(source_lines[2:])).deindent()).splitlines():
            self._body.append(line)

    include = append_body

    @contextmanager
    def _body_context(self, code_formatter):
        yield

    def _write_body(self, code_formatter):
        for line in self._body:
            code_formatter.writeln(line)

    @property
    def source(self):
        buff = StringIO()
        f = CodeFormatter(buff)
        self.write(f)
        return buff.getvalue()
