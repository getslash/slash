# pylint: disable=redefined-outer-name
import pytest
import slash
from slash import ctx, context, Session
from slash.ctx import Context, ContextAttributeProxy
from slash.reporting.null_reporter import NullReporter


@pytest.mark.parametrize('on_stack', [True, False])
def test_context_dir_method_loaded_context(loaded_context, on_stack):
    output = dir(context if on_stack else loaded_context)
    assert 'test_id' in output


def test_context_dir_no_context_loaded():
    assert 'test_id' in dir(context)


def test_null_context_cant_setattr():
    with pytest.raises(AttributeError):
        context.x = 2
    assert not hasattr(context, 'x')


def test_dir_object(loaded_context, queried_context):
    class Object(object):
        x = 2
        y = 3
    loaded_context.test_id = obj = Object()
    assert dir(queried_context.test_id) == dir(obj)


def test_call_object(loaded_context, queried_context):
    value = 'some value'

    def func():
        return value
    loaded_context.test_id = func

    assert queried_context.test_id() == value


def test_null_context():
    assert context.test_id is None
    assert context.result is None


def test_no_session_session_id(loaded_context):
    assert loaded_context.session_id is None


def test_no_session_reporter(loaded_context):
    assert isinstance(loaded_context.reporter, NullReporter)


def test_no_test_test_filename(loaded_context):
    assert loaded_context.test_filename is None


def test_session_context_result():
    with Session() as s:
        assert context.session is s
        assert context.result is s.results.global_result


def test_context_test_filename(suite, suite_test):
    suite_test.append_line('assert slash.context.test_filename == slash.context.test.__slash__.file_path')
    suite.run()


def test_test_context_result(suite):
    for test in suite:
        test.append_line('assert slash.context.result is slash.session.results[slash.context.test]')

    @slash.hooks.result_summary.register  # pylint: disable=no-member
    def assert_result_back_to_normal():  # pylint: disable=unused-variable
        assert context.result is context.session.results.global_result

    assert suite.run().ok()


def test_cannot_pop_bottom():
    assert len(context._stack) == 1  # pylint: disable=protected-access
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
    assert not (contextobj != realobj)  # pylint: disable=superfluous-parens


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
    def cleanup():  # pylint: disable=unused-variable
        while len(context._stack) > 1:  # pylint: disable=protected-access
            context.pop()

@pytest.fixture(params=['global', 'proxy'])
def queried_context(request):
    if request.param == 'global':
        return context
    elif request.param == 'proxy':
        return ctx
    else:
        raise NotImplementedError() # pragma: no cover
