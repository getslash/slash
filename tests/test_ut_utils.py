#pylint: disable=unused-argument
import gc

import pytest
from slash.utils.python import get_arguments


def test_gc_marker(gc_marker):

    class Obj(object):
        pass

    obj = Obj()
    marker = gc_marker.mark(obj)
    assert not marker.destroyed
    del obj
    gc.collect()
    assert marker.destroyed


def test_get_arguments(func):
    args = get_arguments(func)
    assert [a.name for a in args] == ['a', 'b', 'c']



class SampleClass(object):

    def example_func(self, a, b, c):
        pass

def example_func(a, b, c):
    pass

@pytest.fixture(params=[SampleClass.example_func, SampleClass().example_func, example_func])
def func(request):
    return request.param
