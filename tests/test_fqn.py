"""
Test the usage of FQNs in Slash, to uniquely identify tests being run.
"""
import itertools
import os

import slash
from slash.utils.fqn import TestFQN as FQN
from slash.utils.fqn import TestPQN as PQN
from slash.utils.fqn import ModuleTestAddress, InvalidQN
from .utils import TestCase
from .utils import run_tests_assert_success

# needed for nose
FQN.__test__ = PQN.__test__ = False

class FQNTest(TestCase):

    def test_invalid_fqns(self):
        for fqn in [
                "test.py:Factory-1",
                "test.py::Factory",
                "test.py:Factory(1, 2, 3, d=2)",
                "test.py:Factory(1, 2, 3, d=2)()",
                "test.py:Factory.method(1)",
                "test.py:Factory.method(x=f(1, 2, 3))",
                #incompelte FQNs (which are legal PQNs otherwise)
                "test.py:Factory",
                ]:
            try:
                FQN.from_string(fqn)
            except InvalidQN:
                pass
            else:
                self.fail("FQN {0!r} did not fail!".format(fqn))

    
    def test_fqn_equality(self):
        f = FQN("/tmp/test.py", ModuleTestAddress("Factory", "method_name", method_kwargs={"a": 1}, before_kwargs={"b": 2}, after_kwargs={"c": 3}))
        for not_equal in [
                FQN.from_string("/tmp/test.py:Factory2.method_name"),
                FQN.from_string("/tmp/test.py:Factory.method_name"),
                FQN.from_string("/tmp/test.py:Factory.method_name(c=3)"),
                FQN.from_string("/tmp/test.py:Factory(x=1)(y=2).method_name(c=3)"),
                ]:
            self.assertTrue(not_equal != f)
            self.assertTrue(f != not_equal)
            self.assertFalse(f == not_equal)
            self.assertFalse(not_equal == f)
        for equal in [
                FQN.from_string("/tmp/test.py:Factory(b=2)(c=3).method_name(a=1)")
        ]:
            self.assertTrue(f == equal)
            self.assertTrue(equal == f)
            self.assertFalse(f != equal)
            self.assertFalse(equal != f)

class FactoryTestAddressParsingTest(TestCase):

    def test_parameters(self):
        self.assert_parsing(
            "Factory(a=1)(b=2, c=3).method(d=4, e=5)",
            factory_name="Factory",
            method_name="method",
            before_kwargs={"a": 1},
            method_kwargs={"d": 4, "e": 5},
            after_kwargs={"b": 2, "c": 3})

    def test_parameters_strings(self):
        self.assert_parsing(
            "Factory(a='string, with, comma')().method(b='another, string,')",
            factory_name="Factory",
            before_kwargs={"a": 'string, with, comma'},
            method_name="method",
            after_kwargs={},
            method_kwargs={"b": 'another, string,'})

    def test_fqn_insensitive_parameter_ordering(self):
        parse = ModuleTestAddress.from_string
        self.assertEquals(parse("F(a=1, b=2)(c=3, d=4).meth(e=5, f=6)"),
                          parse("F(b=2,a=1)(d=4,c=3).meth(f=6,e=5)"))

    def assert_parsing(self, expr, **fields):
        result = ModuleTestAddress.from_string(expr)
        for field_name, value in fields.items():
            actual_value = getattr(result, field_name)
            if actual_value != value:
                self.fail("Field {0!r} in result differs (expected: {1!r}, got {2!r})".format(
                    field_name, value, actual_value))

class PQNTest(TestCase):

    def test_is_simple_path(self):
        self.assertTrue(PQN.from_string("/tmp/testme.py").is_simple_path())
        self.assertFalse(PQN.from_string("/tmp/testme.py:bla").is_simple_path())

    def test_pyc_files_original_exists(self):
        "Filenames ending with .pyc should be normalized to .py"
        original = os.path.join(self.get_new_path(), "testme.py")
        with open(original, "w"):
            pass
        f = PQN(original+"c")
        self.assertEquals(f.path, original)

    def test_pyc_files_original_missing(self):
        "When the original python file is missing and the filename ends with .pyc, it should not be fixed"
        original = os.path.join(self.get_new_path(), "testme.pyc")
        f = PQN(original)
        self.assertEquals(f.path, original)


    def test_matching_filename(self):
        for pattern in ["/tmp/testme.py:Blap", "/tmp/testme.py", "/tmp/testme.py:Blap.method"]:
            self._assert_matches(pattern, "/tmp/testme.py:Blap.method")
            self._assert_matches(pattern, "/tmp/testme.py:Blap(a=1)(b=2).method(c=3)")
            self._assert_matches(pattern, "/tmp/testme.py:Blap.method(c=3)")
            self._assert_not_matches(pattern, "/tmp/testme2.py:F.method")
            self._assert_not_matches(pattern, "/tmp/testme2.py:F(a=1)(b=2).method(c=3)")

    def test_matching_factory(self):
        self._assert_matches("/tmp/testme.py:Factory", "/tmp/testme.py:Factory.method(a=1)")
        self._assert_matches("/tmp/testme.py:Factory", "/tmp/testme.py:Factory.method")
        self._assert_not_matches("/tmp/testme.py:Factory", "/tmp/testme.py:Factory2.method")
        self._assert_not_matches("/tmp/testme.py:Factory", "/tmp/testme2.py:Factory.method")

    def test_matching_methods(self):
        self._assert_matches("/tmp/testme.py:Factory.method", "/tmp/testme.py:Factory.method")
        self._assert_not_matches("/tmp/testme.py:Factory.method", "/tmp/testme2.py:Factory.method")
        self._assert_not_matches("/tmp/testme.py:Factory.method", "/tmp/testme.py:Factory.method2")
        self._assert_not_matches("/tmp/testme.py:Factory.method", "/tmp/testme.py:Factory2.method")
        self._assert_not_matches("/tmp/testme.py:Factory", "/tmp/testme2.py:Factory.method")

    def test_matching_parameters(self):
        for before, after, params in [
                ("(a=1)", "()", "()"),
                ("()", "(d=4)", "()"),
                ("()", "(d=4)", "(f=6)"),
                ("()", "(d=4)", "(f=6, e=5)"),
                ("(a=1, b=2)", "(d=4)", "(f=6, e=5)"),
                ("(a=1, b=2)", "(d=4, c=3)", "(f=6, e=5)"),
                ]:
            pqn = "/tmp/testme.py:Factory{0}{1}.method{2}".format(before, after, params)
            self._assert_matches(pqn, "/tmp/testme.py:Factory(a=1, b=2)(c=3, d=4).method(e=5, f=6)")
            self._assert_not_matches(pqn, "/tmp/testme.py:Factory2(a=1, b=2)(c=3, d=4).method(e=5, f=6)")
            self._assert_not_matches(pqn, "/tmp/testme.py:Factory(a=1, b=2)(c=3, d=4).method2(e=5, f=6)")
            self._assert_not_matches(pqn, "/tmp/testme.py:Factory(a=2, b=2)(c=3, d=5).method(e=5, f=7)")

    def test_invalid_pqns(self):
        for pqn in [
                "test.py:Factory-1",
                "test.py::Factory",
                "test.py:Factory(1, 2, 3, d=2)",
                "test.py:Factory(1, 2, 3, d=2)()",
                "test.py:Factory.method(1)",
                "test.py:Factory.method(x=f(1, 2, 3))",
                ]:
            try:
                PQN.from_string(pqn)
            except InvalidQN:
                pass
            else:
                self.fail("Pattern {0!r} did not fail!".format(pqn))

    def _assert_not_matches(self, p, f):
        self._assert_matches(p, f, positive=False)

    def _assert_matches(self, p, f, positive=True):
        pqn = PQN.from_string(p)
        fqn = FQN.from_string(f)

        if pqn.matches(fqn) != positive:
            msg = "does not match" if positive else "unexpectedly matches"
            self.fail("PQN {0!r} {1} FQN {2!r}".format(pqn, msg, fqn))

    def test_repr(self):
        for pattern in ["/tmp/blap:bla", "/tmp/a.py", "kjlkjdfd"]:
            self.assertEquals(repr(PQN.from_string(pattern)), pattern)
