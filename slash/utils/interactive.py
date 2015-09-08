from __future__ import print_function

import threading
from contextlib import contextmanager
from ..ctx import context
from ..core import metadata
from ..core.function_test import FunctionTestFactory

try:
    from IPython import embed # pylint: disable=F0401
except ImportError:
    import code
    def _interact(ns):
        code.interact(local=ns)
else:
    def _interact(ns):
        embed(user_ns=ns)

def start_interactive_shell(**namespace):
    """
    Starts an interactive shell. Uses IPython if available, else fall back
    to the native Python interpreter.

    Any keyword argument specified will be available in the shell ``globals``.
    """
    if context.g is not None:
        namespace.update(context.g.__dict__)

    _interact(namespace)

def _start_interactive_test():
    return start_interactive_shell()

def generate_interactive_test():
    [returned] = FunctionTestFactory(_start_interactive_test).generate_tests(context.session.fixture_store)
    m = returned.__slash__ = metadata.Metadata(None, returned, '')
    returned.__slash__.mark_interactive()
    m.factory_name = m.address = 'Interactive'
    return returned

@contextmanager
def notify_if_slow_context(message, slow_seconds=1):
    evt = threading.Event()
    def notifier():
        if not evt.wait(timeout=slow_seconds) and context.session is not None:
            context.session.reporter.report_message(message)
    thread = threading.Thread(target=notifier)
    thread.start()
    try:
        yield
    finally:
        evt.set()
        thread.join()
