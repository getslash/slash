from .utils import TestCase
import itertools
import os
import sys

_module_name_generator = ("custom_module_{}".format(x) for x in itertools.count())

class ExtHookTest(TestCase):
    def setUp(self):
        super(ExtHookTest, self).setUp()
        self.path = self.get_new_path()
        self.addCleanup(setattr, sys, "path", list(sys.path))
        sys.path.insert(0, self.path)
        self.expected_value = 31337
        self.module_name = next(_module_name_generator)

        with open(os.path.join(self.path, "slash_{}.py".format(self.module_name)), "w") as f:
            f.write("value = {!r}".format(self.expected_value))

    def test_ext_hook_import(self):
        module = __import__("slash.ext.{}".format(self.module_name), fromlist=[''])
        self.assertEqual(module.value, self.expected_value)

    def test_slash_ext(self):
        from slash import ext   # pylint: disable=unused-variable

    def test_ext_hook_import_nonexistent(self):
        with self.assertRaises(ImportError):
            from slash.ext import nonexistent  # pylint: disable=unused-variable, no-name-in-module
