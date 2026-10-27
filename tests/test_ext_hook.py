from .utils import TestCase
import itertools
import os
import sys

_module_name_generator = (f"custom_module_{x}" for x in itertools.count())


class ExtHookTest(TestCase):
    def setUp(self):
        super().setUp()
        self.path = self.get_new_path()
        self.addCleanup(setattr, sys, "path", list(sys.path))
        sys.path.insert(0, self.path)
        self.expected_value = 31337
        self.module_name = next(_module_name_generator)

        with open(os.path.join(self.path, f"slash_{self.module_name}.py"), "w") as f:
            f.write(f"value = {self.expected_value!r}")

    def test_ext_hook_import(self):
        module = __import__(f"slash.ext.{self.module_name}", fromlist=[""])
        self.assertEqual(module.value, self.expected_value)

    def test_slash_ext(self):
        from slash import ext  # pylint: disable=unused-variable,unused-import  # noqa: F401

    def test_ext_hook_import_nonexistent(self):
        with self.assertRaises(ImportError):
            from slash.ext import nonexistent  # pylint: disable=unused-variable,no-name-in-module,unused-import  # noqa: F401
