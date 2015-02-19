import pytest
import slash


def test_frame_order(error, use_exception):
    code_line = error.traceback.frames[-1].code_line.strip()
    if use_exception:
        assert code_line == '1 / 0'
    else:
        assert code_line == 'get_error_adder()("error message")'


@pytest.fixture
def error(get_error_adder, use_exception):

    def f1():
        try:
            g1()
        except ZeroDivisionError:
            assert use_exception
            get_error_adder()()

    def g1():
        h1()

    def h1():
        if use_exception:
            1 / 0
        else:
            get_error_adder()("error message")

    with slash.Session() as s:
        f1()
    [err] = s.results.global_result.get_errors()
    return err


@pytest.fixture(params=[lambda: slash.add_error, lambda: slash.context.result.add_error])
def get_error_adder(request):
    return request.param


@pytest.fixture(params=[True, False])
def use_exception(request):
    return request.param
