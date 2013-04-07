from .utils.callback import Callback

session_start = Callback(doc="Called right after session starts")
session_end = Callback(doc="Called right before the session ends, regardless of the reason for termination")

suite_start = Callback(doc="Called right after a suite starts")
suite_end = Callback(doc="Called right before the suite ends, regardless of the reason for termination")

result_summary = Callback(doc="Called at the end of the execution, when printing results")

exception_caught_before_debugger = Callback(
    doc="Called whenever an exception is caught, but a debugger hasn't been entered yet"
)
exception_caught_after_debugger = Callback(
    doc="Called whenever an exception is caught, and a debugger has already been run"
)
