import ast
import os
from .._compat import string_types, iteritems

class TestPQN(object):
    """
    Represents a partially qualified name of a test.

    This can be thought of as a pattern to be matched against real FQNs
    """

    def __init__(self, path, address_in_module=None):
        super(TestPQN, self).__init__()
        assert address_in_module is None or isinstance(address_in_module, ModuleTestAddress), \
            "address_in_module must be a ModuleTestAddress object"
        self.path = path
        self.address_in_module = address_in_module
        self.path, self.abspath = self._normalize_paths(path)

        self.fqn = self.path

        if self.address_in_module is not None:
            self.fqn += ":{0}".format(self.address_in_module.to_string())

    def _normalize_paths(self, path):
        if path.endswith(".pyc"):
            non_pyc = path[:-1]
            if os.path.isfile(non_pyc):
                path = non_pyc
        abspath = os.path.abspath(path)
        path = os.path.relpath(abspath, ".")

        if path.startswith(".."):
            path = abspath

        return path, abspath

    @classmethod
    def from_string(cls, s):
        path = s
        address_in_module = None
        if ":" in path:
            path, address_in_module = path.split(":", 1)
            address_in_module = ModuleTestAddress.from_string(address_in_module)

        return cls(
            path=path, address_in_module=address_in_module)

    def is_simple_path(self):
        """
        Returns True if this pattern simply leads to a single path on the filesystem, rather than a partial match inside the file/directory
        """
        return self.address_in_module is None

    def matches(self, other):
        if not isinstance(other, TestFQN):
            return False

        if self.path != other.path:
            return False

        if self.address_in_module is not None:
            for address_field_name in ("factory_name", "method_name"):
                address_field_value = getattr(self.address_in_module, address_field_name)
                if address_field_value is not None and address_field_value != getattr(other.address_in_module, address_field_name):
                    return False

            for keywords_field_name in ("before_kwargs", "after_kwargs", "method_kwargs"):
                pattern_kwargs = getattr(self.address_in_module, keywords_field_name)
                other_kwargs = getattr(other.address_in_module, keywords_field_name)
                if not all(other_kwargs.get(arg_name, _NOTHING) == arg_value
                           for arg_name, arg_value in iteritems(pattern_kwargs)):
                    return False

        return True

    def __repr__(self):
        return self.fqn

_NOTHING = object()

class TestFQN(TestPQN):
    """
    Represents a fully-qualified name of a test being run
    """
    def __init__(self, path, address_in_module):
        if address_in_module is None or not address_in_module.is_complete():
            raise InvalidQN()
        super(TestFQN, self).__init__(path, address_in_module)

    def __eq__(self, other):
        if type(other) is not TestFQN and not isinstance(other, string_types):
            return NotImplemented

        return str(self) == str(other)

    def __ne__(self, other):
        return not self == other

class ModuleTestAddress(object):
    """
    Represents the 'address' of a test inside the factory that generated it
    """

    def __init__(self, factory_name, method_name=None, before_kwargs=None, after_kwargs=None, method_kwargs=None):
        super(ModuleTestAddress, self).__init__()
        self.factory_name = factory_name
        self.method_name = method_name
        self.before_kwargs = before_kwargs or {}
        self.after_kwargs = after_kwargs or {}
        self.method_kwargs = method_kwargs or {}

    def is_complete(self):
        return self.factory_name is not None and self.method_name is not None

    @classmethod
    def from_string(cls, s):
        try:
            node = ast.parse(s)
        except SyntaxError:
            raise InvalidQN()
        if len(node.body) != 1 or not isinstance(node.body[0], ast.Expr):
            raise InvalidQN()
        node = node.body[0].value
        return ModuleTestAddress(**_parse_test_module_address_ast(node))

    def to_string(self):
        returned = self.factory_name
        if self.before_kwargs or self.after_kwargs:
            returned += "{0}{1}".format(
                self._get_call_string(self.before_kwargs),
                self._get_call_string(self.after_kwargs),
            )
        if self.method_name is not None:
            returned += ".{0}".format(self.method_name)
            if self.method_kwargs:
                returned += self._get_call_string(self.method_kwargs)
        return returned

    def _get_call_string(self, call):
        if not call:
            return ""
        return "({0})".format(", ".join("{0}={1!r}".format(k, v) for k, v in iteritems(call)))

    def __eq__(self, other):
        if type(other) is not ModuleTestAddress:
            return NotImplemented

        return all(getattr(self, x) == getattr(other, x) for x in
                   ("factory_name", "method_name", "before_kwargs", "after_kwargs", "method_kwargs"))

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return self.to_string()

def _parse_test_module_address_ast(node):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Call):
            # factory call
            return _parse_factory_class_ast(node)
        elif isinstance(node.func, ast.Attribute):
            # method call
            returned = _parse_method_ast(node.func)
            returned["method_kwargs"] = _parse_call(node)
        else:
            raise InvalidQN()
    elif isinstance(node, ast.Attribute):
        # method getting
        returned = _parse_factory_class_ast(node.value)
        returned["method_name"] = node.attr
    elif isinstance(node, ast.Name):
        returned = {"factory_name":  node.id, "method_name": None}
    else:
        raise InvalidQN()
    return returned

def _parse_method_ast(node):
    returned = _parse_factory_class_ast(node.value)
    returned["method_name"] = node.attr
    return returned

def _parse_factory_class_ast(node):
    returned = {}
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Call) or not isinstance(node.func.func, ast.Name):
            raise InvalidQN()

        returned["after_kwargs"] = _parse_call(node)
        returned["before_kwargs"] = _parse_call(node.func)
        returned["factory_name"] = node.func.func.id
    elif isinstance(node, ast.Name):
        returned["factory_name"] = node.id
    else:
        raise InvalidQN()
    return returned

def _parse_call(node):
    if node.args or node.starargs or node.kwargs:
        raise InvalidQN()
    try:
        return dict((kw.arg, ast.literal_eval(kw.value)) for kw in node.keywords)
    except ValueError:
        raise InvalidQN()


class InvalidQN(ValueError):
    def __init__(self):
        super(InvalidQN, self).__init__("Invalid FQN given")
