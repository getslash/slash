from shakedown import exception_handling
from forge import Anything
from .utils import (
    TestCase,
    CustomException,
    )

class ExceptionMarksTest(TestCase):
    def test__exception_mark(self):
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
    def test__handling_exceptions(self):
        with self.assertRaises(CustomException) as caught:
            with exception_handling.handling_exceptions():
                with exception_handling.handling_exceptions():
                    with exception_handling.handling_exceptions():
                        raise self.raised
        self.assertIs(caught.exception, self.raised)
