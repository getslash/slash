from .utils import TestCase
import slash

class FixtureTest(TestCase):
    hook_called = False
    identifier = object()
    def test_fixture_exists_on_session_start(self):
        @slash.exception_handling.disable_exception_swallowing
        def _on_session_start():
            self.assertIsNotNone(slash.fixture)
            slash.fixture.value = "value"
            self.assertEquals(slash.fixture.value, "value")
            self.hook_called = True
        slash.hooks.session_start.register(_on_session_start, self.identifier)
        self.addCleanup(
            slash.hooks.session_start.unregister_by_identifier,
            self.identifier
        )
        with slash.session.Session():
            pass
        self.assertTrue(self.hook_called)
