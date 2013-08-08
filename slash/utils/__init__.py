import functools
from ..exceptions import SkipTest
from ..runnable_test_factory import RunnableTestFactory

def skip_test(*args):
    """
    Skips the current test execution by raising a :class:`slash.exceptions.SkipTest`
    exception. It can optionally receive a reason argument.
    """
    raise SkipTest(*args)

def skipped(thing, reason=None):
    """
    A decorator for skipping methods and classes
    """
    if isinstance(thing, str):
        return functools.partial(skipped, reason=thing)
    if isinstance(thing, type) and issubclass(thing, RunnableTestFactory):
        thing.skip_all(reason)
        return thing

    @functools.wraps(thing)
    def new_func(*_, **__): # pylint: disable=unused-argument
        skip_test(reason)
    return new_func
