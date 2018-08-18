# pylint: disable=redefined-outer-name,unused-variable
import json
import os
import types

import emport

import dessert
import pytest
from slash.core.error import Error
from slash.exception_handling import mark_exception_frame_correction

from .utils import without_pyc


def test_error_exception_str_repr(error):
    assert "NotImplementedError" in str(error)
    assert "NotImplementedError" in repr(error)


def test_detailed_exception(error):
    assert error.get_detailed_str()
    assert 'NotImplementedError' in error.get_detailed_str()


def test_error_filename(error):
    assert error.filename == without_pyc(os.path.abspath(__file__))


def test_error_func_name(error):
    assert error.func_name == "func_3"


def test_code_string(error):
    assert error.cause.code_line == "    raise NotImplementedError()"
    assert error.cause.code_string == """def func_3():

    local_func_3 = global_func_3
    raise NotImplementedError()\n"""


def test_error_exc_info(error):
    assert error.exc_info is not None
    assert isinstance(error.exc_info, tuple)
    assert error.exc_info[0] is NotImplementedError
    assert isinstance(error.exc_info[1], NotImplementedError)
    assert isinstance(error.exc_info[2], types.TracebackType)


def test_error_forget_exc_info(error):
    error.forget_exc_info()
    assert error.exc_info is None


def test_error_exc_info_forgotten_by_default(suite, suite_test):
    suite_test.when_run.error()
    res = suite.run()[suite_test]
    [err] = res.get_errors()
    assert err.exc_info is None


def test_error_frame_objects(error):
    assert error.traceback.frames
    for f in error.traceback.frames:
        assert isinstance(f.python_frame, types.FrameType)


def test_error_frame_objects_forgotten_by_default(suite, suite_test):
    suite_test.when_run.error()
    res = suite.run()[suite_test]
    [err] = res.get_errors()
    assert err.traceback.frames
    for frame in err.traceback.frames:
        assert frame.python_frame is None


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_frame_locals(error):
    assert error.traceback.frames[-3].locals == {
        "local_func_1": {
            "value": "'global_func_1'"
        }}


def test_to_list(error):
    serialized = error.traceback.to_list()
    assert serialized[-3]['locals'] == {
        "local_func_1": {
            "value": "'global_func_1'"
        }}
    # Just make sure that it's serializable
    json.dumps(serialized)


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_frame_locals_no_assertion_markers(assertion_error):
    for var_name, _ in assertion_error.cause.locals.items():
        assert "@" not in var_name


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_frame_globals(error):
    assert error.traceback.frames[-3].globals == {
        "global_func_1": {
            "value": "'global_func_1'"
        }}


def test_capture_exception_twice_caches_object():
    try:
        try:
            raise RuntimeError()
        except RuntimeError:
            err1 = Error.capture_exception()
            raise
    except RuntimeError:
        err2 = Error.capture_exception()

    assert err1 is err2


def test_detailed_traceback(error):
    detailed = error.get_detailed_str()
    assert detailed


def test_error_is_fatal(error):
    assert not error.is_fatal()


def test_error_mark_fatal(error):
    rv = error.mark_fatal()
    assert rv is error
    assert error.is_fatal()


def test_error_frame_correction():

    class CustomException(Exception):
        pass

    def f():
        g()

    def g():
        h()

    def h():
        raise mark_exception_frame_correction(CustomException(), +2)

    try:
        f()
    except CustomException:
        err = Error.capture_exception()

    assert err.traceback.frames[-1].func_name == 'f'


####


@pytest.fixture
def error():
    try:
        func_1()
    except:
        return Error.capture_exception()
    else:
        assert False, "Did not fail"


@pytest.fixture
def non_exception_error():
    def func1():
        return func2()

    def func2():
        return Error('some_error')

    err = func1()
    return err


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


@pytest.fixture
def assertion_error(tmpdir):
    filename = tmpdir.join("file.py")
    filename.write("""
def f(x):
    return x

def g(x):
    return x

def func():
    assert f(g(1)) == g(f(2))""")

    with dessert.rewrite_assertions_context():
        module = emport.import_file(str(filename))

    try:
        module.func()
    except:
        return Error.capture_exception()
    else:
        assert False, "Did not fail"
