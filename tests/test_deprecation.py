import logbook

import pytest
from slash.utils import deprecated


def test_deprecated_func_called(capture):
    assert deprecated_func(1, 2) == 3

def test_deprecation_message(capture):
    deprecated_func(1, 2)

    [record] = capture.records
    assert "deprecated" in record.message
    assert 'deprecated_func' in record.message

def test_deprecation_with_message(capture):

    @deprecated("use something else instead")
    def func(a, b):
        return a + b

    func(1, 2)

    [record] = capture.records
    assert "use something else instead" in record.message
    assert "func is deprecated" in record.message

def test_deprecations_different_sources(capture):

    def f():
        deprecated_func(1, 2)

    def g():
        deprecated_func(1, 2)

    f()
    g()
    assert len(capture.records) == 2

def test_deprecations_same_sources(capture):

    def f():
        deprecated_func(1, 2)

    f()
    f()
    assert len(capture.records) == 1


@pytest.fixture
def capture(request):
    handler = logbook.TestHandler(level=logbook.WARNING)
    handler.push_application()

    @request.addfinalizer
    def pop():
        handler.pop_application()
    return handler

@deprecated
def deprecated_func(a, b):
    return a + b
