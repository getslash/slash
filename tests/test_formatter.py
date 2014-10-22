from slash._compat import cStringIO
from slash.utils.formatter import Formatter
from slash.utils.color_string import ColorString
from .utils import TestCase


class FormatterTest(TestCase):

    def setUp(self):
        super(FormatterTest, self).setUp()
        self.buff = cStringIO()
        self.f = Formatter(self.buff)

    def assertOutput(self, v):
        self.assertEquals(self.buff.getvalue(), v)

    def test_write_non_strings(self):
        class MyObject(object):

            def __repr__(self):
                return 'repr'

            def __str__(self):
                return 'str'
        self.f.write("1:")
        self.f.write(MyObject())
        self.f.write("2:")
        self.f.writeln(MyObject())
        self.assertOutput("1:str2:str\n")

    def test_write_writeln(self):
        self.f.writeln("hello")
        self.assertOutput("hello\n")
        self.f.write("a")
        self.f.write("bcd")
        self.assertOutput("hello\nabcd")

    def test_indent_write_writeln(self):
        with self.f.indented():
            self.f.writeln("hello")
            self.assertOutput(" hello\n")
            self.f.write("a")
            self.f.write("bcd")
            self.f.writeln()
            self.assertOutput(" hello\n abcd\n")

    def test_empty_writeln(self):
        self.f.writeln('a')
        self.f.writeln()
        self.f.writeln()
        self.f.writeln('b')
        self.assertOutput('a\n\n\nb\n')

    def test_multiline_write(self):
        self.f.writeln('a\nb')
        with self.f.indented(3, string='.'):
            self.f.writeln('c\n d\ne')
        self.f.writeln('f')
        self.assertOutput("a\nb\n...c\n... d\n...e\nf\n")

    def test_indentation(self):
        self.f.writeln("begin")
        with self.f.indented(3):
            self.f.writeln("a")
            self.f.writeln("b")
        self.f.writeln("end")
        self.assertOutput("begin\n   a\n   b\nend\n")

    def test_indentation_different_char_through_ctor(self):
        self._test__indentation_different_char(True)

    def test_indentation_different_char_not_through_ctor(self):
        self._test__indentation_different_char(False)

    def _test__indentation_different_char(self, through_constructor):
        if through_constructor:
            self.f = Formatter(self.buff, indentation_string='*')
            indenter = self.f.indented
        else:
            indenter = lambda indentation: self.f.indented(
                indentation, string='*')
        self.f.writeln("a")
        with indenter(2):
            self.f.writeln('b')
        self.f.writeln('c')
        self.assertOutput('a\n**b\nc\n')


class FormatterColorTest(TestCase):

    def setUp(self):
        super(FormatterColorTest, self).setUp()
        self.buff = self.forge.create_wildcard_mock()
        self.buff.write("").whenever()  # indentation of 0

    def test_color_string_tty(self):
        self.buff.isatty().whenever().and_return(True)
        s = ColorString("hello", "red")
        self.buff.write(s.get_colored())
        self.forge.replay()
        Formatter(self.buff).write(s)

    def test_color_string_not_tty(self):
        self.buff.isatty().whenever().and_return(False)
        s = ColorString("hello", "red")
        self.buff.write("hello")
        self.forge.replay()
        Formatter(self.buff).write(s)
