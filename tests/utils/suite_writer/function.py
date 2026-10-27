import collections
import itertools
from contextlib import contextmanager
from uuid import uuid4
from .code_element import CodeElement
from .parameter import Parameter

_FixtureSpec = collections.namedtuple("_FixtureSpec", ["alias_name", "fixture", "alias_with_attribute"])


class Function(CodeElement):
    def __init__(self, suite, name=None):
        super().__init__(suite)
        self._name = name
        self._decorators = []
        self._parameters = []
        self._additional_parameter_string = ""
        self._fixtures = []
        self._events = []
        self._deferred_events = []

    def add_parameter_string(self, s):
        self._additional_parameter_string += s

    def add_decorator(self, decorator_string):
        self._decorators.append(decorator_string)

    def get_fixtures(self):
        return [f for _, f, _ in self._fixtures]

    def get_parameters(self):
        return self._parameters

    def add_parameter(self, *args, **kwargs):
        returned = Parameter(self.suite, *args, **kwargs)
        self._parameters.append(returned)
        return returned

    def depend_on_fixture(self, f, alias=False, alias_with_attribute=False):
        alias_name = "alias_{}".format(str(uuid4()).replace("-", "")) if alias else None
        self._fixtures.append(_FixtureSpec(alias_name, f, alias_with_attribute))
        return f

    def _write_event(self, code_formatter, eventcode):
        if self.suite.debug_info:
            code_formatter.writeln(f"__ut__.events.add({eventcode!r}, {self.id!r})")

    def add_deferred_event(self, decorator=None, name="deferred", extra_code=(), adder=None):
        event = f"{name}_{uuid4()}"
        self._deferred_events.append({"decorator": decorator, "event": event, "extra_code": extra_code, "adder": adder})
        return event

    def add_event(self, name="event"):
        event = f"{name}_{uuid4()}"
        self._events.append(event)
        return (event, self.id)

    @contextmanager
    def _body_context(self, code_formatter):
        self._write_decorators(code_formatter)
        code_formatter.writeln(f"def {self._get_function_name()}({self._get_parameter_string()}):")

        with code_formatter.indented():
            if not self.suite.debug_info:
                code_formatter.writeln("pass")
            self._write_parameter_values(code_formatter)
            self._write_immediate_events(code_formatter)
            self._write_deferred_events(code_formatter)
            self._write_prologue(code_formatter)
            yield
            self._write_epilogue(code_formatter)
            self._write_return(code_formatter)
        code_formatter.writeln()

    def _get_parameter_string(self):
        returned = ", ".join(self._get_argument_strings())
        if returned and self._additional_parameter_string:
            returned += ", "
        returned += self._additional_parameter_string
        return returned

    def _write_prologue(self, code_formatter):
        pass

    def _write_epilogue(self, code_formatter):
        pass

    def _write_immediate_events(self, code_formatter):
        for event in self._events:
            self._write_event(code_formatter, event)

    def _write_deferred_events(self, code_formatter):
        if not self.suite.debug_info:
            return
        for index, deferred in enumerate(self._deferred_events, 1):
            deferred_func_name = f"_deferred{index}"
            adder = deferred["adder"]
            if adder is None:
                code_formatter.writeln(f"@{deferred['decorator']}")
            code_formatter.writeln(f"def {deferred_func_name}():")
            with code_formatter.indented():
                code_formatter.writeln(f"__ut__.events.add({deferred['event']!r})")
                for line in deferred["extra_code"]:
                    code_formatter.writeln(line)
            if adder is not None:
                code_formatter.write(adder.format(deferred_func_name))
            code_formatter.writeln()

    def _write_return(self, code_formatter):
        pass

    def _write_decorators(self, code_formatter):
        for d in self._decorators:
            code_formatter.write("@")
            code_formatter.writeln(d)
        for p in self._parameters:
            p.write_decorator(code_formatter)

    def _write_parameter_values(self, code_formatter):
        if (not self.suite.debug_info) and (not self.suite.is_parallel):
            return

        for p in self._iter_notify_parameters():
            if self.suite.is_parallel:
                code_formatter.writeln(
                    f"slash.context.result.data.setdefault('param_values', {{}})[{p.id!r}] = {p.name}"
                )
            else:
                code_formatter.writeln(f"__ut__.notify_parameter_value({p.id!r}, {p.name})")

    def _iter_notify_parameters(self):
        return itertools.chain(self._parameters, (f for _, f, _ in self._fixtures if f.is_generator_fixture()))

    def _get_function_name(self):
        if self._name is None:
            raise NotImplementedError()  # pragma: no cover
        return self._name

    @property
    def name(self):
        return self._get_function_name()

    def _get_argument_strings(self):
        for p in self._parameters:
            yield p.name
        for alias, f, alias_with_attribute in self._fixtures:
            if alias is not None:
                if alias_with_attribute:
                    yield f"{alias}: slash.use.{f.name}"
                else:
                    yield f"{alias}: slash.use({f.name!r})"
            else:
                yield f.name


class Method(Function):
    def _get_argument_strings(self):
        return itertools.chain(["self"], super()._get_argument_strings())
