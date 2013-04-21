from .utils import TestCase
import shakedown

class FixtureTest(TestCase):
    hook_called = False
    identifier = object()
    def test_fixture_exists_on_session_start(self):
        @shakedown.exception_handling.disable_exception_swallowing
        def _on_session_start():
            self.assertIsNotNone(shakedown.fixture)
            shakedown.fixture.value = "value"
            self.assertEquals(shakedown.fixture.value, "value")
            self.hook_called = True
        shakedown.hooks.session_start.register(_on_session_start, self.identifier)
        self.addCleanup(
            shakedown.hooks.session_start.unregister_by_identifier,
            self.identifier
        )
        with shakedown.session.Session():
            pass
        self.assertTrue(self.hook_called)
