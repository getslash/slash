class TestFailed(AssertionError):
    """
    This exception class distinguishes actual test failures (mostly assertion errors,
    but possibly other conditions as well) from regular asserts.

    This is important, since regular code that is tested can use asserts, and that
    should not be considered a test failure (but rather a code failure)
    """
    pass
