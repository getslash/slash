from ..exceptions import SkipTest

def skip_test(*args):
    """
    Skips the current test execution by raising a :class:`shakedown.exceptions.SkipTest`
    exception. It can optionally receive a reason argument.
    """
    raise SkipTest(*args)
