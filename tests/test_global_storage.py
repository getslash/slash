import gossip
import slash

from .utils import TestCase


class GlobalStorageTest(TestCase):
    hook_called = False
    token = object()
    def test_global_storage_exists_on_session_start(self):
        @slash.exception_handling.disable_exception_swallowing
        def _on_session_start():
            self.assertIsNotNone(slash.g)
            slash.g.value = "value"
            self.assertEquals(slash.g.value, "value")
            self.hook_called = True
        slash.hooks.session_start.register(_on_session_start, token=self.token)
        self.addCleanup(
            gossip.unregister_token,
            self.token
        )
        with slash.Session() as s:
            with s.get_started_context():
                pass
        self.assertTrue(self.hook_called)
