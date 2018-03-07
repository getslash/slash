from slash._compat import izip_longest
from uuid import uuid4

from .element import Element


class Parameter(Element):

    def __init__(self, suite, num_values=3, values=None):
        super(Parameter, self).__init__(suite)
        self.name = 'param_{0}'.format(self.id)
        if values is None:
            values = [str(uuid4()) for _ in range(num_values)]
        self.values = values
        self.labels = []

    def write_decorator(self, code_formatter):
        code_formatter.writeln('@slash.parametrize({0!r}, {1})'.format(
            self.name, self._format_values()))

    def _format_values(self):
        returned = '['
        for label, value in izip_longest(self.labels, self.values):
            assert value is not None
            if label is None:
                returned += repr(value)
            else:
                returned += 'slash.param({!r}, {!r})'.format(label, value)
            returned += ', '
        returned += ']'
        return returned


    def add_labels(self):
        assert not self.labels
        self.labels = ['label_{}'.format(str(uuid4()).replace('-', '_')[:20]) for value in self.values]
