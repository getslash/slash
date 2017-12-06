import py.code  # pylint: disable=no-name-in-module, import-error

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

    def _add_body(self, code_element, prepend):
        """An easier way to write multiline injected code:

        @code_element.append_body
        def __code__():
            some_code_line()
            for i in range(20):
                some_other_code()
        """
        source_lines = str(py.code.Code(code_element).source()).splitlines()  # pylint: disable=no-member
        assert source_lines[0].startswith('@')
        assert source_lines[1].startswith('def ')
        assert source_lines[2][0].isspace()
        lines = str(py.code.Source('\n'.join(source_lines[2:])).deindent()).splitlines() # pylint: disable=no-member
        if prepend:
            self._body[:0] = lines
        else:
            self._body.extend(lines)

    def append_body(self, code_element):
        self._add_body(code_element, prepend=False)
    include = append_body

    def prepend_body(self, code_element):
        self._add_body(code_element, prepend=True)

    @contextmanager  # pylint: disable=unused-argument
    def _body_context(self, code_formatter):  # pylint: disable=unused-argument
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
