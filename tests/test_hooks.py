import gossip.exceptions
import gossip.hooks
import vintage
from slash import hooks

from .utils import TestCase


class CustomHooksTest(TestCase):

    def setUp(self):
        super(CustomHooksTest, self).setUp()
        self.hook_name = "some_custom_hook"
        with vintage.get_no_deprecations_context():
            self.hook = hooks.add_custom_hook(self.hook_name)

    def tearDown(self):
        with vintage.get_no_deprecations_context():
            hooks.remove_custom_hook(self.hook_name)
        self.assertFalse(hasattr(hooks, self.hook_name))
        super(CustomHooksTest, self).tearDown()

    def test_hooks_are_globally_available_through_hooks_module(self):
        self.assertIsInstance(hooks.some_custom_hook, gossip.hooks.Hook)  # pylint: disable=no-member
        self.assertIs(hooks.some_custom_hook, self.hook)  # pylint: disable=no-member

    def test_ensure_custom_hook(self):
        with vintage.get_no_deprecations_context():
            self.assertIs(hooks.ensure_custom_hook(self.hook_name), self.hook)
            new_hook = hooks.ensure_custom_hook("new_custom_hook")
            @self.addCleanup
            def _cleanup():
                with vintage.get_no_deprecations_context():
                    hooks.remove_custom_hook("new_custom_hook")
            self.assertIs(new_hook, hooks.new_custom_hook)  # pylint: disable=no-member

    def test_hooks_appear_in_get_all_hooks(self):
        with vintage.get_no_deprecations_context():
            all_hooks = dict(hooks.get_all_hooks())
        self.assertIs(all_hooks[self.hook_name], self.hook)

    def test_cannot_reinstall_hook_twice(self):
        with vintage.get_no_deprecations_context(), \
            self.assertRaises(gossip.exceptions.NameAlreadyUsed):
            hooks.add_custom_hook(self.hook_name)

    def test_cannot_install_default_hooks(self):
        with vintage.get_no_deprecations_context(), \
            self.assertRaises(gossip.exceptions.NameAlreadyUsed):
            hooks.add_custom_hook("test_start")
