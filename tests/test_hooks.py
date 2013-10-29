from .utils import TestCase
from slash import hooks, exceptions

class CustomHooksTest(TestCase):

    def setUp(self):
        super(CustomHooksTest, self).setUp()
        self.hook_name = "some_custom_hook"
        self.hook = hooks.add_custom_hook(self.hook_name)

    def tearDown(self):
        hooks.remove_custom_hook(self.hook_name)
        self.assertFalse(hasattr(hooks, self.hook_name))
        super(CustomHooksTest, self).tearDown()

    def test_hooks_are_globally_available_through_hooks_module(self):
        self.assertIsInstance(hooks.some_custom_hook, hooks.Callback)
        self.assertIs(hooks.some_custom_hook, self.hook)

    def test_ensure_custom_hook(self):
        self.assertIs(hooks.ensure_custom_hook(self.hook_name), self.hook)
        new_hook = hooks.ensure_custom_hook("new_custom_hook")
        self.addCleanup(hooks.remove_custom_hook, "new_custom_hook")
        self.assertIs(new_hook, hooks.new_custom_hook)

    def test_ensure_custom_hook_does_not_allow_built_in_hooks(self):
        with self.assertRaises(exceptions.HookAlreadyExists):
            hooks.ensure_custom_hook("test_start")

    def test_hooks_appear_in_get_all_hooks(self):
        all_hooks = dict(hooks.get_all_hooks())
        self.assertIs(all_hooks[self.hook_name], self.hook)

    def test_get_custom_hook_names(self):
        self.assertEquals(hooks.get_custom_hook_names(), [self.hook_name])

    def test_cannot_reinstall_hook_twice(self):
        with self.assertRaises(exceptions.HookAlreadyExists):
            hooks.add_custom_hook(self.hook_name)

    def test_cannot_install_default_hooks(self):
        with self.assertRaises(exceptions.HookAlreadyExists):
            hooks.add_custom_hook("test_start")

