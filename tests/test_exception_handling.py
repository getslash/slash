import sys
import gossip
import pytest
import inspect
import traceback
import slash
from slash import exception_handling
from slash._compat import ExitStack, PYPY
from slash.exceptions import SkipTest, TestFailed
from slash.utils import debug

from .utils import CustomException, TestCase


def test_handling_exceptions_swallow_skip_test(suite, suite_test):

    @suite_test.append_body
    def __code__():             # pylint: disable=unused-variable
        from slash.exception_handling import handling_exceptions
        with handling_exceptions(swallow=True):
            slash.skip_test()
        __ut__.events.add('NEVER') # pylint: disable=undefined-variable

    suite_test.expect_skip()

    summary = suite.run()
    assert not summary.events.has_event('NEVER')


def test_passthrough_types():

    value = CustomException()

    with slash.Session():
        with pytest.raises(CustomException) as caught:
            with exception_handling.handling_exceptions(passthrough_types=(CustomException,)):
                raise value
    assert value is caught.value
    assert not exception_handling.is_exception_handled(value)

    with slash.Session():
        with pytest.raises(CustomException) as caught:
            with exception_handling.handling_exceptions(passthrough_types=(AttributeError,)):
                raise value
    assert value is caught.value
    assert exception_handling.is_exception_handled(value)


def test_swallow_types():
    value = CustomException()

    with slash.Session():
        with exception_handling.handling_exceptions(swallow_types=(CustomException,)):
            raise value
    assert sys.exc_info() == exception_handling.NO_EXC_INFO


class FakeTracebackTest(TestCase):
    def setUp(self):
        super(FakeTracebackTest, self).setUp()
        self.override_config("debug.enabled", True)
        self.forge.replace_with(debug, "launch_debugger", self.verify_fake_traceback_debugger)
        self.debugger_called = False
        self._tb_len = 0

    @pytest.mark.skipif(PYPY, reason='Cannot run on PyPy')
    def test_fake_traceback(self):
        with slash.Session(), pytest.raises(ZeroDivisionError):
            with exception_handling.handling_exceptions(fake_traceback=False):
                self._expected_line_number = inspect.currentframe().f_lineno + 1
                a = 1 / 0
                return a

        with slash.Session(), pytest.raises(ZeroDivisionError):
            with exception_handling.handling_exceptions():
                self._expected_line_number = inspect.currentframe().f_lineno + 1
                a = 1 / 0
                return a

    def verify_fake_traceback_debugger(self, exc_info):
        assert traceback.extract_tb(exc_info[2])[-1][1] == self._expected_line_number
        if not self._tb_len:
            # First attempt, no fake traceback
            self._tb_len = self._get_tb_len(exc_info[2])
            assert self._tb_len != 0
        else:
            # Second attempt, with fake traceback
            assert self._tb_len < self._get_tb_len(exc_info[2])

    def _get_tb_len(self, tb):
        tb_len = 0
        while tb:
            tb_len += 1
            tb = tb.tb_next
        return tb_len


def test_handling_exceptions():
    value = CustomException()

    with slash.Session(), pytest.raises(CustomException) as caught:
        with exception_handling.handling_exceptions():
            with exception_handling.handling_exceptions():
                with exception_handling.handling_exceptions():
                    raise value
    assert caught.value is value


@pytest.mark.skipif(sys.version_info >= (3, 0), reason='Cannot run on 3.x')
def test_reraise_after_exc_info_reset():
    @gossip.register('slash.exception_caught_before_debugger')
    def exception_hook():       # pylint: disable=unused-variable
        sys.exc_clear()

    with slash.Session(), pytest.raises(CustomException):
        with exception_handling.handling_exceptions():
            raise CustomException()



class DebuggingTest(TestCase):

    def setUp(self):
        super(DebuggingTest, self).setUp()
        self.forge.replace_with(debug, "launch_debugger", self.dummy_debugger)
        self.debugger_called = False

    def dummy_debugger(self, *args, **kwargs):
        self.debugger_called = True

    def test_debugging_not_configured(self):
        self._raise_exception_in_context(ZeroDivisionError)
        self.assertFalse(self.debugger_called)

    def test_debugging_configured_no_skips(self):
        self.override_config("debug.debug_skips", False)
        self.override_config("debug.enabled", True)
        self._raise_exception_in_context(SkipTest)
        self.assertFalse(self.debugger_called)

    def test_debugging_skips(self):
        self.override_config("debug.debug_skips", True)
        self.override_config("debug.enabled", True)
        self._raise_exception_in_context(SkipTest)
        self.assertTrue(self.debugger_called)

    def _raise_exception_in_context(self, exception_type):
        with slash.Session(), self.assertRaises(exception_type):
            with exception_handling.handling_exceptions():
                raise exception_type()


def test_swallow_exceptions():
    with exception_handling.get_exception_swallowing_context():
        raise CustomException("!!!")


def test_no_swallow():
    raised = CustomException()
    with pytest.raises(CustomException) as caught:
        with exception_handling.get_exception_swallowing_context():
            raise exception_handling.noswallow(raised)
    assert raised is caught.value


def test_disable_exception_swallowing_function():
    raised = CustomException()
    with pytest.raises(CustomException) as caught:
        with exception_handling.get_exception_swallowing_context():
            exception_handling.disable_exception_swallowing(raised)
            raise raised
    assert caught.value is raised


def test_disable_exception_swallowing_decorator():
    raised = CustomException()
    @exception_handling.disable_exception_swallowing
    def func():
        raise raised
    with pytest.raises(CustomException) as caught:
        with exception_handling.get_exception_swallowing_context():
            func()
    assert caught.value is raised


@pytest.mark.parametrize('message', [None, 'My custom message'])
@pytest.mark.parametrize('exc_types', [CustomException, (CustomException, ZeroDivisionError)])
def test_assert_raises(exc_types, message):
    raised = CustomException()
    with slash.Session():
        with slash.assert_raises(exc_types, msg=message) as caught:
            raise raised
    assert sys.exc_info() == exception_handling.NO_EXC_INFO
    assert caught.exception is raised


@pytest.mark.parametrize('message', [None, 'My custom message'])
def test_assert_raises_that_not_raises(message):
    expected_substring = message or 'not raised'
    try:
        with slash.assert_raises(Exception, msg=message):
            pass
    except TestFailed as e:
        assert expected_substring in str(e)
    else:
        raise Exception('TestFailed exception was not raised :()')


@pytest.mark.parametrize('with_session', [True, False])
def test_handling_exceptions_inside_assert_raises_with_session(with_session):
    value = CustomException()

    with ExitStack() as ctx:

        if with_session:
            session = ctx.enter_context(slash.Session())
            ctx.enter_context(session.get_started_context())
        else:
            session = None

        with slash.assert_raises(CustomException):
            with exception_handling.handling_exceptions():
                raise value

    assert not exception_handling.is_exception_handled(value)
    if with_session:
        assert session.results.get_num_errors() == 0

