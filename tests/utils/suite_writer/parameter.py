from itertools import zip_longest
from uuid import uuid4

from .element import Element


class Parameter(Element):
    def __init__(self, suite, num_values=3, values=None):
        super().__init__(suite)
        self.name = f"param_{self.id}"
        if values is None:
            values = [str(uuid4()) for _ in range(num_values)]
        self.values = values
        self.labels = []

    def write_decorator(self, code_formatter):
        code_formatter.writeln(f"@slash.parametrize({self.name!r}, {self._format_values()})")

    def _format_values(self):
        returned = "["
        for label, value in zip_longest(self.labels, self.values):
            assert value is not None
            if label is None:
                returned += repr(value)
            else:
                returned += f"slash.param({label!r}, {value!r})"
            returned += ", "
        returned += "]"
        return returned

    def add_labels(self):
        assert not self.labels
        self.labels = ["label_{}".format(str(uuid4()).replace("-", "_")[:20]) for value in self.values]
