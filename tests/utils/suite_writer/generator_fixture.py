from uuid import uuid4

from .function import Function


class GeneratorFixture(Function):
    def __init__(self, suite, file, num_values=3):
        super().__init__(suite)
        self.file = file
        self.values = [str(uuid4()) for _ in range(num_values)]

    def is_generator_fixture(self):
        return True

    def _write_decorators(self, code_formatter):
        code_formatter.writeln("@slash.generator_fixture")
        super()._write_decorators(code_formatter)

    def _get_function_name(self):
        return f"fx_{self.id}"

    def _write_return(self, code_formatter):
        for value in self.values:
            code_formatter.writeln(f"yield {value!r}")

    def _get_argument_strings(self):
        return []

    def __repr__(self):
        return f"<Generator Fixture {self.name}>"
