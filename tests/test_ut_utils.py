# pylint: disable=unused-argument,redefined-outer-name
import gc

import pytest
from slash.utils.python import get_arguments


def test_gc_marker(gc_marker):
    class Obj:
        pass

    obj = Obj()
    marker = gc_marker.mark(obj)
    assert not marker.destroyed
    del obj
    gc.collect()
    assert marker.destroyed


def test_get_arguments(func):
    args = get_arguments(func)
    assert [a.name for a in args] == ["a", "b", "c"]


def test_get_arguments_pypy_code_path(func, monkeypatch):
    # inspect.getargspec, which this code path used to call, was removed in Python 3.11
    monkeypatch.setattr("slash.utils.python.PYPY", True)
    args = get_arguments(func)
    assert [a.name for a in args] == ["a", "b", "c"]


class SampleClass:
    def example_func(self, a, b, c):
        pass


def example_func(a, b, c):
    pass


@pytest.fixture(params=[SampleClass.example_func, SampleClass().example_func, example_func])
def func(request):
    return request.param
