
class SlashException(Exception):
    pass

class HookAlreadyExists(SlashException):
    pass

class NoActiveSession(SlashException):
    pass

class CannotLoadTests(SlashException):
    pass

class TestFailed(AssertionError):
    """
    This exception class distinguishes actual test failures (mostly assertion errors,
    but possibly other conditions as well) from regular asserts.

    This is important, since regular code that is tested can use asserts, and that
    should not be considered a test failure (but rather a code failure)
    """
    pass

class SkipTest(Exception):
    """
    This exception should be raised in order to interrupt the execution of the currently running test, marking
    it as skipped
    """
    def __init__(self, reason="Test skipped"):
        super(SkipTest, self).__init__(reason)
        self.reason = reason
