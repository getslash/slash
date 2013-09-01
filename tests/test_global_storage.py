from .utils import TestCase
import slash

class GlobalStorageTest(TestCase):
    hook_called = False
    identifier = object()
    def test_global_storage_exists_on_session_start(self):
        @slash.exception_handling.disable_exception_swallowing
        def _on_session_start():
            self.assertIsNotNone(slash.g)
            slash.g.value = "value"
            self.assertEquals(slash.g.value, "value")
            self.hook_called = True
        slash.hooks.session_start.register(_on_session_start, self.identifier)
        self.addCleanup(
            slash.hooks.session_start.unregister_by_identifier,
            self.identifier
        )
        with slash.Session():
            pass
        self.assertTrue(self.hook_called)
