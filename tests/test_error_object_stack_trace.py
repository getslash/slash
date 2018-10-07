# pylint: disable=pointless-statement,redefined-outer-name
import pytest
import slash


def test_frame_order(error, use_exception):
    code_line = error.traceback.frames[-1].code_line.strip()
    if use_exception:
        assert code_line == '1 / 0'
    else:
        assert code_line == 'get_error_adder()("error message")'


@pytest.mark.usefixtures('disable_vintage_deprecations')
def test_self_variables(error):
    frame = error.traceback.frames[-3]
    assert frame.func_name == 'method1'
    assert 'ExampleObject' in frame.locals['self']['value']
    assert frame.locals['self.a']['value'] == '1'
    assert frame.locals['self.b']['value'] == '2'
    for var_name in frame.locals:
        assert not var_name.startswith('self.__')


@pytest.fixture
def error(get_error_adder, use_exception):

    def f1():
        obj = ExampleObject()
        try:
            obj.method1()
        except ZeroDivisionError:
            assert use_exception
            get_error_adder()()



    class ExampleObject(object):

        def __init__(self):
            self.a = 1
            self.b = 2

        def method1(self):
            g1()


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
