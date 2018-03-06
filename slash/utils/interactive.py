from __future__ import print_function

import threading
import time
import datetime
from contextlib import contextmanager
from .. import hooks
from ..conf import config
from ..ctx import context
from ..core import metadata
from ..core.function_test import FunctionTestFactory
from ..exceptions import TerminatedException
from ..exception_handling import handle_exception

from IPython.terminal.embed import embed  # pylint: disable=F0401

def _interact(ns):
    def _handle_exception(shell, exc_type, exc_value, exc_tb, tb_offset):
        exc_info = (exc_type, exc_value, exc_tb)
        shell.showtraceback(exc_info, tb_offset)
        if not _is_exception_in_ipython_eval(exc_tb):
            handle_exception(exc_info)
        if isinstance(exc_value, TerminatedException):
            context.result.add_error('Terminated')
            shell.exit_now = True

    embed(user_ns=ns, display_banner=False, custom_exceptions=((Exception, TerminatedException), _handle_exception))


def _is_exception_in_ipython_eval(exc_tb):
    while exc_tb.tb_next is not None:
        exc_tb = exc_tb.tb_next
    return exc_tb.tb_frame.f_code.co_filename.startswith('<')

def start_interactive_shell(**namespace):
    """
    Starts an interactive shell. Uses IPython if available, else fall back
    to the native Python interpreter.

    Any keyword argument specified will be available in the shell ``globals``.
    """
    if context.g is not None and config.root.interactive.expose_g_globals:
        namespace.update(context.g.__dict__)

    hooks.before_interactive_shell(namespace=namespace)  # pylint: disable=no-member
    _interact(namespace)

def _start_interactive_test():
    return start_interactive_shell()

def generate_interactive_test():
    [returned] = FunctionTestFactory(_start_interactive_test).generate_tests(context.session.fixture_store)
    returned.__slash__ = metadata.Metadata(None, returned)
    returned.__slash__.allocate_id()
    returned.__slash__.mark_interactive()
    return returned

def _humanize_time_delta(seconds):
    return str(datetime.timedelta(seconds=seconds)).partition('.')[0]

@contextmanager
def notify_if_slow_context(message, slow_seconds=1, end_message=None, show_duration=True):
    evt = threading.Event()
    evt.should_report_end_msg = False
    def notifier():
        if not evt.wait(timeout=slow_seconds) and context.session is not None:
            context.session.reporter.report_message(message)
            evt.should_report_end_msg = True
    thread = threading.Thread(target=notifier)
    start_time = time.time()
    thread.start()

    try:
        yield
    finally:
        evt.set()
        thread.join()
        if evt.should_report_end_msg and end_message is not None:
            if show_duration:
                end_message += ' (took {})'.format(_humanize_time_delta(time.time() - start_time))
            context.session.reporter.report_message(end_message)
