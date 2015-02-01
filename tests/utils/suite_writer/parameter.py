from uuid import uuid4

from .element import Element


class Parameter(Element):

    def __init__(self, suite, num_values=3):
        super(Parameter, self).__init__(suite)
        self.name = 'param_{0}'.format(self.id)
        self.values = [str(uuid4()) for i in range(num_values)]

    def write_decorator(self, code_formatter):
        code_formatter.writeln('@slash.parametrize({0!r}, {1!r})'.format(
            self.name, self.values))

