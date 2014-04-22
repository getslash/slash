import os

import pytest
from slash.core.error import Error


def test_error_exception_str_repr(error):
    assert "NotImplementedError" in str(error)
    assert "NotImplementedError" in repr(error)

def test_error_filename(error):
    assert error.filename == os.path.abspath(__file__)

def test_error_func_name(error):
    assert error.func_name == "func_3"

def test_code_string(error):
    assert error.cause.code_line == "    raise NotImplementedError()"
    assert error.cause.code_string == """def func_3():

    local_func_3 = global_func_3
    raise NotImplementedError()\n"""

def test_frame_locals(error):
    assert error.traceback.frames[-3].locals == {
        "local_func_1": {
            "value": "'global_func_1'"
        }}

def test_frame_globals(error):
    assert error.traceback.frames[-3].globals == {
        "global_func_1": {
            "value": "'global_func_1'"
        }}


####

@pytest.fixture
def error():
    try:
        func_1()
    except:
        return Error.capture_exception()

global_func_1 = "global_func_1"
global_func_2 = "global_func_2"
global_func_3 = "global_func_3"

def func_1():
    local_func_1 = global_func_1

    func_2()

def func_2():
    local_func_2 = global_func_2

    func_3()

def func_3():

    local_func_3 = global_func_3
    raise NotImplementedError()
