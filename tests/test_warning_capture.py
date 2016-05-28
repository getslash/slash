import warnings
from slash.utils.warning_capture import warning_callback_context

def test_warning_capture_context():
    captured = []

    def callback(*args, **kwargs):
        captured.append(Warning(*args, **kwargs))

    with warning_callback_context(callback):
        warnings.warn('some warning')

    assert len(captured) == 1
    [w] = captured # pylint: disable=unbalanced-tuple-unpacking
    assert w.args[0].args[0] == 'some warning'

class Warning(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
