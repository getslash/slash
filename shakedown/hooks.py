from .utils.callback import Callback

suite_start = Callback(doc="Happens right after a suite starts")
suite_end = Callback(doc="Happens right before the suite ends, regardless of status of termination")


