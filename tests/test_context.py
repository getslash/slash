from uuid import uuid1

import pytest
from slash import context
from slash.ctx import Context, ContextAttributeProxy


def test_null_context():
    assert context.test_id is None

def test_cannot_pop_bottom():
    assert len(context._stack) == 1
    with pytest.raises(RuntimeError):
        context.pop()

def test_push_context(loaded_context):
    test_id = loaded_context.test_id = "some_test_id"
    assert context.test_id == test_id

def test_object_proxy_getattr(contextobj, realobj):
    assert contextobj.attr is realobj.attr
    assert contextobj.__attr__ is realobj.__attr__
    assert not hasattr(contextobj, "nonexisting")
    assert not hasattr(contextobj, "__nonexisting__")

def test_object_proxy_eq(contextobj, realobj):
    assert contextobj == realobj

def test_object_proxy_ne(contextobj, realobj):
    assert not (contextobj != realobj)

def test_object_proxy_str_repr(contextobj, realobj):
    assert str(contextobj) == str(realobj)
    assert repr(contextobj) == repr(realobj)

@pytest.fixture
def contextobj(loaded_context, realobj):
    setattr(loaded_context, "obj", realobj)
    return ContextAttributeProxy("obj")

@pytest.fixture
def realobj():
    class Object(object):

        __attr__ = object()
        attr = object()

    return Object()

@pytest.fixture
def loaded_context():
    returned = Context()
    context.push(returned)
    return returned

@pytest.fixture(autouse=True, scope="function")
def pop_all(request):
    @request.addfinalizer
    def cleanup():
        while len(context._stack) > 1:
            context.pop()
