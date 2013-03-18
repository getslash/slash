from .utils.callback import Callback

suite_start = Callback(doc="Called right after a suite starts")
suite_end = Callback(doc="Called right before the suite ends, regardless of status of termination")

result_summary = Callback(doc="Called at the end of the execution, when printing results")

exception_caught_before_debugger = Callback(
    doc="Called whenever an exception is caught, but a debugger hasn't been entered yet"
)
exception_caught_after_debugger = Callback(
    doc="Called whenever an exception is caught, and a debugger has already been run"
)
