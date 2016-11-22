
class SlashException(Exception):

    @classmethod
    def throw(cls, *args, **kwargs):
        raise cls(*args, **kwargs)


class TerminatedException(BaseException):
    pass

INTERRUPTION_EXCEPTIONS = (KeyboardInterrupt, TerminatedException)


class NoActiveSession(SlashException):
    pass


class CannotLoadTests(SlashException):
    pass

CLI_ABORT_EXCEPTIONS = (CannotLoadTests, )


class FixtureException(CannotLoadTests):
    pass


class CyclicFixtureDependency(FixtureException):
    pass


class UnresolvedFixtureStore(FixtureException):
    pass


class UnknownFixtures(FixtureException):
    pass


class InvalidFixtureScope(FixtureException):
    pass


class IncorrectScope(SlashException):
    pass


class InvalidTest(SlashException):
    pass


class CannotAddCleanup(SlashException):
    pass


class TestFailed(AssertionError):

    """
    This exception class distinguishes actual test failures (mostly assertion errors,
    but possibly other conditions as well) from regular asserts.

    This is important, since regular code that is tested can use asserts, and that
    should not be considered a test failure (but rather a code failure)
    """
    pass


FAILURE_EXCEPTION_TYPES = (TestFailed, AssertionError)


class SkipTest(SlashException):

    """
    This exception should be raised in order to interrupt the execution of the currently running test, marking
    it as skipped
    """

    def __init__(self, reason="Test skipped"):
        super(SkipTest, self).__init__(reason)
        self.reason = reason
