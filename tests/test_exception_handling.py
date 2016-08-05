import sys
import gossip
import pytest
import slash
from slash import exception_handling
from slash._compat import ExitStack
from slash.exceptions import SkipTest
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

    with pytest.raises(CustomException) as caught:
        with exception_handling.handling_exceptions(passthrough_types=(CustomException,)):
            raise value
    assert value is caught.value
    assert not exception_handling.is_exception_handled(value)

    with pytest.raises(CustomException) as caught:
        with exception_handling.handling_exceptions(passthrough_types=(AttributeError,)):
            raise value
    assert value is caught.value
    assert exception_handling.is_exception_handled(value)


def test_swallow_types():
    value = CustomException()

    with exception_handling.handling_exceptions(swallow_types=(CustomException,)):
        raise value


def test_handling_exceptions():
    value = CustomException()

    with pytest.raises(CustomException) as caught:
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

    with pytest.raises(CustomException):
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
        with self.assertRaises(exception_type):
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

