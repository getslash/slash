# pylint: disable=redefined-outer-name
import pytest
from slash._compat import PY2

if PY2:
    from slash.utils.python import wraps
else:
    from functools import wraps

from slash.utils.python import call_all_raise_first, resolve_underlying_function


def test_call_all_raise_first(funcs):
    exc_type = funcs[2].raise_when_called()

    with pytest.raises(exc_type):
        call_all_raise_first(funcs)

    for index, func in enumerate(funcs):  # pylint: disable=unused-variable
        assert func.called_count == 1


@pytest.fixture
def funcs():

    class Func(object):

        called_count = 0
        exc_type = None

        def __call__(self):
            self.called_count += 1
            if self.exc_type is not None:
                raise self.exc_type()

        def raise_when_called(self):
            class CustomException(Exception):
                pass

            self.exc_type = CustomException
            return self.exc_type

    return [Func() for _ in range(10)]


@pytest.mark.parametrize('class_method', [True, False])
def test_resolve_underlying_function_method(class_method):
    if class_method:
        decorator = classmethod
    else:
        decorator = lambda f: f

    class Blap(object):

        @decorator
        def method(self):
            pass

    resolved = resolve_underlying_function(Blap.method)
    assert resolved is resolve_underlying_function(Blap.method) # stable
    assert not hasattr(resolved, '__func__')
    assert resolved.__name__ == 'method'


@pytest.mark.parametrize('thing', [object(), object, None, 2, "string"])
def test_resolve_underlying_function_method_no_op(thing):
    assert resolve_underlying_function(thing) is thing


def _example_decorator(func):
    @wraps(func)
    def new_func():
        pass

    return new_func

def test_resolve_underlying_decorator_regular_func():

    def orig():
        pass
    decorated = _example_decorator(orig)
    assert resolve_underlying_function(decorated) is orig

def test_resolve_underlying_decorator_method():

    class Blap(object):

        def orig(self):
            pass

        decorated = _example_decorator(orig)

    assert resolve_underlying_function(Blap.decorated) is resolve_underlying_function(Blap.orig)
    assert resolve_underlying_function(Blap.decorated).__name__ == 'orig'
