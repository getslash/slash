from .utils import (
    TestCase,
    CustomException,
    )
from contextlib import contextmanager
from forge import Anything
from slash import exception_handling
from slash.utils import debug
from slash.exceptions import SkipTest

class ExceptionMarksTest(TestCase):
    def test_exception_mark(self):
        e = CustomException()
        mark = object()
        self.assertFalse(exception_handling.is_exception_marked(e, "a"))
        self.assertFalse(exception_handling.is_exception_marked(e, "b"))
        exception_handling.mark_exception(e, "a", mark)
        self.assertTrue(exception_handling.is_exception_marked(e, "a"))
        self.assertFalse(exception_handling.is_exception_marked(e, "b"))
        self.assertIs(exception_handling.get_exception_mark(e, "a"), mark)

class HandlingExceptionsContextTest(TestCase):
    def setUp(self):
        super(HandlingExceptionsContextTest, self).setUp()
        self.handler = self.forge.create_wildcard_mock()
        self.forge.replace_with(exception_handling, "_EXCEPTION_HANDLERS", [self.handler])
        # expect handler to be called once!
        self.raised = CustomException()
        self.handler((CustomException, self.raised, Anything()))
        self.forge.replay()
    def test_handling_exceptions(self):
        with self.assertRaises(CustomException) as caught:
            with exception_handling.handling_exceptions():
                with exception_handling.handling_exceptions():
                    with exception_handling.handling_exceptions():
                        raise self.raised
        self.assertIs(caught.exception, self.raised)

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

class ExceptionSwallowingTest(TestCase):
    def test_swallow(self):
        with exception_handling.get_exception_swallowing_context():
            raise CustomException("!!!")
    def test_no_swallow(self):
        with self.assertNoSwallow() as raised:
            raise exception_handling.noswallow(raised)
    def test_disable_exception_swallowing_function(self):
        with self.assertNoSwallow() as raised:
            exception_handling.disable_exception_swallowing(raised)
            raise raised
    def test_disable_exception_swallowing_decorator(self):
        @exception_handling.disable_exception_swallowing
        def func():
            raise raised
        with self.assertNoSwallow() as raised:
            func()
    @contextmanager
    def assertNoSwallow(self):
        raised = CustomException()
        with self.assertRaises(CustomException) as caught:
            with exception_handling.get_exception_swallowing_context():
                yield raised
        self.assertIs(raised, caught.exception)
