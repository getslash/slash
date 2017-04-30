import warnings

import pytest

import slash
from slash import Session

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


def test_session_adds_simple_filter(request):
    @request.addfinalizer
    def cleanup():              # pylint: disable=unused-variable
        warnings.simplefilter('default')
    warnings.simplefilter('ignore')
    with Session() as s:
        warnings.warn('bla')

    assert len(s.warnings.warnings) == 1

def test_session_warning_calls_hook():
    notified = []

    @slash.hooks.warning_added.register # pylint: disable=no-member
    def warning_added(warning):         # pylint: disable=unused-variable
        notified.append(warning)

    with Session() as session:
        warnings.warn('bla')

    assert list(session.warnings) == notified != []


def test_cant_reenter_twice():
    ctx = warning_callback_context(no_op)
    with ctx:
        with pytest.raises(RuntimeError):
            with ctx:
                pass

def test_cant_exit_no_enter():
    ctx = warning_callback_context(no_op)
    with pytest.raises(RuntimeError):
        ctx.__exit__(None, None, None)


def no_op(*args, **kwargs):     # pylint: disable=unused-argument
    pass

class Warning(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
