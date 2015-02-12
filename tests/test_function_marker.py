import pytest
from slash.utils.function_marker import function_marker


def test_marked_func_identical_to_original(marker, func):
    orig_func = func
    new_func = marker(func)
    assert orig_func is new_func

def test_is_marked(marker, func):
    assert not marker.is_marked(func)
    marker(func)
    assert marker.is_marked(func)

@pytest.mark.parametrize('value', [True, False, 'value', 2.0])
def test_marker_value(func, value):

    marker = function_marker('bla')

    func = marker(value)(func)

    assert marker.is_marked(func)
    assert marker.get_value(func) == value

def test_marker_value_does_not_exist(func):
    with pytest.raises(LookupError):
        function_marker('bla').get_value(func)

    assert function_marker('bla').get_value(func, 1) == 1

def test_marker_on_methods(marker):

    class Obj(object):

        @marker
        def marked_func(self):
            pass

        def unmarked_func(self):
            pass

        @classmethod
        def unmarked_classmethod(self):
            pass

        @staticmethod
        def unmarked_staticmethod(self):
            pass

        @marker
        @classmethod
        def marked_classmethod(self):
            pass

        @marker
        @staticmethod
        def marked_staticmethod(self):
            pass


    for subject in (Obj, Obj()):
        for name in dir(subject):
            if name.startswith('_'):
                continue
            method = getattr(subject, name)
            assert 'marked' in name
            if 'unmarked' in name:
                assert not marker.is_marked(method)
            else:
                assert marker.is_marked(method)

@pytest.fixture
def marker():
    return function_marker('some_marker')

@pytest.fixture
def func():
    def returned():
        pass
    return returned
