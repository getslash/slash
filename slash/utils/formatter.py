from __future__ import print_function
from contextlib import contextmanager
import errno

from .color_string import ColorString


class Formatter(object):

    def __init__(self, stream, indentation_string=" "):
        super(Formatter, self).__init__()
        self._indentation_string = indentation_string
        self._indentation_list = []
        self._indentation = ""
        self._stream = LineTracker(stream)
        self._isatty = stream.isatty()

    def write_separator(self, length=80):
        self.writeln("-" * length)

    def writeln(self, *args, **kwargs):
        self.write(end="\n", *args, **kwargs)

    def write(self, *args, **kwargs):
        try:
            end = kwargs.pop('end', '')
            for arg in args:
                if isinstance(arg, ColorString):
                    if self._isatty:
                        arg = arg.get_colored()
                    else:
                        arg = str(arg)
                lines = str(arg).splitlines()
                for index, line in enumerate(lines):
                    if self._stream.is_line_empty():
                        self._stream.write(self._indentation)
                    self._stream.write(line)
                    if index != len(lines) - 1:
                        self._stream.write("\n")
            self._stream.write(end)
        except IOError as e:
            if e.errno not in (errno.EIO, errno.EPIPE):
                raise

    def indent(self):
        self._indent(1)

    def dedent(self):
        self._indent(-1)

    def _indent(self, increment, string=None):
        if string is None:
            string = self._indentation_string
        if increment < 0:
            del self._indentation_list[increment:]
        else:
            self._indentation_list.extend(string for x in range(increment))
        self._indentation = ''.join(self._indentation_list)

    @contextmanager
    def indented(self, increment=1, string=None):
        self._indent(increment=increment, string=string)
        try:
            yield
        finally:
            self._indent(increment=-increment)


class LineTracker(object):

    def __init__(self, stream):
        super(LineTracker, self).__init__()
        self._stream = stream
        self._empty_line = True

    def write(self, output):
        self._stream.write(output)
        if output:
            self._empty_line = output.endswith('\n')

    def is_line_empty(self):
        return self._empty_line
