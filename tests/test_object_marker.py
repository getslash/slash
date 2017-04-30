# pylint: disable=redefined-outer-name
import pytest
from slash.utils.marks import get_marks, mark, try_get_mark


def test_mark(marked_obj, mark_name, mark_value):
    assert get_marks(marked_obj) == {mark_name: mark_value}


def test_mark_immutable(marked_obj, mark_name, mark_value):
    marks = get_marks(marked_obj)
    marks["1"] = ["2"]
    assert get_marks(marked_obj) == {mark_name: mark_value}


def test_try_get_mark(marked_obj, mark_name, mark_value):
    assert try_get_mark(marked_obj, mark_name) == mark_value


def test_try_get_mark_fail(marked_obj):
    assert try_get_mark(marked_obj, "nonexistent") is None


def test_try_get_mark_fail_with_default(marked_obj):
    _default = object()
    assert try_get_mark(marked_obj, "nonexistent", _default) is _default

def test_mark_append():

    class Obj(object):
        pass

    mark_name = 'some_mark'
    assert try_get_mark(Obj, mark_name) is None
    assert mark(mark_name, 'mark_value', append=True)(Obj) is Obj
    assert get_marks(Obj) == {mark_name: ['mark_value']}

@pytest.mark.parametrize('obj', [1, None, object(), type, "string"])
def test_try_get_mark_fail_non_marked(obj):
    assert try_get_mark(obj, "mark") is None

### Boilerplate ###

mark_factories = []

markfactory = mark_factories.append


@markfactory
def markfactory_class(mark_name, mark_value):
    @mark(mark_name, mark_value)
    class Blap(object):
        pass

    return Blap


@markfactory
def markfactory_func(mark_name, mark_value):
    @mark(mark_name, mark_value)
    def func():
        pass

    return func


@markfactory
def method(mark_name, mark_value):
    class Blap(object):

        @mark(mark_name, mark_value)
        def func(self):
            pass

    return Blap.func


@pytest.fixture(params=mark_factories)
def marked_obj(request, mark_name, mark_value):
    returned = request.param(mark_name, mark_value)
    return returned


@pytest.fixture(params=['mark_name'])
def mark_name(request):
    return request.param


@pytest.fixture(params=['mark_value', 1, True, 1.0])
def mark_value(request):
    return request.param
