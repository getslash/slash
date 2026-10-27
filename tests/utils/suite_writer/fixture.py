from uuid import uuid4
import itertools

from .function import Function


class Fixture(Function):
    def __init__(self, suite, file, scope=None, autouse=False, name=None):
        if name is None:
            name = "fx_{}".format(str(uuid4()).replace("-", "")[:6])
        super().__init__(suite, name=name)
        self.file = file
        self.scope = scope
        self.autouse = autouse

    def is_generator_fixture(self):
        return False

    def add_cleanup(self, **kwargs):
        return self.add_deferred_event("this.add_cleanup", name="fixture_cleanup", **kwargs)

    def _write_decorators(self, code_formatter):
        self._write_fixture_decorator(code_formatter)
        super()._write_decorators(code_formatter)

    def _write_prologue(self, code_formatter):
        if not self.suite.debug_info:
            return

        self._write_event(code_formatter, "fixture_start")
        code_formatter.writeln(f"__ut__.notify_fixture_start({self.id!r}, {self.get_value_string()})")
        code_formatter.writeln("@this.add_cleanup")
        code_formatter.writeln("def cleanup():")
        with code_formatter.indented():
            self._write_event(code_formatter, "fixture_end")
            code_formatter.writeln(f"__ut__.notify_fixture_end({self.id!r})")

        super()._write_prologue(code_formatter)

    def _write_return(self, code_formatter):
        code_formatter.writeln(f"return {self.get_value_string()}")

    def _write_fixture_decorator(self, code_formatter):
        params = {}
        if self.scope is not None:
            params["scope"] = self.scope
        if self.autouse:
            params["autouse"] = True

        code_formatter.write("@slash.fixture")
        if params:
            code_formatter.write("({})".format(", ".join(f"{k}={v!r}" for k, v in params.items())))
        code_formatter.writeln()

    def get_value_string(self):
        returned = f'{{"value": {self.name!r}, "params": {{'

        for name, param in itertools.chain(
            ((p.name, p) for p in self._parameters),
            ((alias or f.name, f) for alias, f, _ in self._fixtures),
        ):
            returned += f"{param.id!r}: {name},"
        returned += "} }"
        return returned

    def _get_argument_strings(self):
        return itertools.chain(["this"], super()._get_argument_strings())

    def __repr__(self):
        return f"<Fixture {self.name}>"
