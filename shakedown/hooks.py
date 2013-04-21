from .utils.callback import Callback
import six

session_start = Callback(doc="Called right after session starts")
session_end   = Callback(doc="Called right before the session ends, regardless of the reason for termination")

suite_start = Callback(doc="Called right after a suite starts")
suite_end   = Callback(doc="Called right before the suite ends, regardless of the reason for termination")

test_start   = Callback(doc="Called right after a test starts")
test_end     = Callback(doc="Called right before a test ends, regardless of the reason for termination")
test_success = Callback(doc="Called on test success")
test_error   = Callback(doc="Called on test error")
test_failure = Callback(doc="Called on test failure")
test_skip    = Callback(doc="Called on test skip")

result_summary = Callback(doc="Called at the end of the execution, when printing results")

exception_caught_before_debugger = Callback(
    doc="Called whenever an exception is caught, but a debugger hasn't been entered yet"
)
exception_caught_after_debugger = Callback(
    doc="Called whenever an exception is caught, and a debugger has already been run"
)

def get_all_hooks():
    for name, callback in six.iteritems(globals()):
        if not isinstance(callback, Callback):
            continue
        yield name, callback
