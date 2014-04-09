from .utils import TestCase
from .utils import CustomException
from slash.utils.callback import Callback, requires, RequirementsNotMet

class CallbackTestBase(TestCase):
    def setUp(self):
        super(CallbackTestBase, self).setUp()
        self.hook = Callback(["arg_value"])
        self.arg = object()

class CallbackTest(CallbackTestBase):
    def test_cannot_call_with_positionals(self):
        with self.assertRaises(TypeError):
            self.hook(1)
    def test_callback(self):
        callback1 = self.forge.create_wildcard_function_stub()
        callback2 = self.forge.create_wildcard_function_stub()
        self.hook.register(callback1)
        self.hook.register(callback2)
        # expect
        callback1(arg_value=self.arg)
        callback2(arg_value=self.arg)
        self.forge.replay()
        self.hook(arg_value=self.arg)
    def test_callback_registering_via_decorator(self):
        handler = self.forge.create_wildcard_function_stub()
        @self.hook.register
        def proxy(arg_value):
            handler(arg_value=arg_value)

        self.assertIsNotNone(proxy)
        #expect
        handler(arg_value=self.arg)
        self.forge.replay()
        self.hook(arg_value=self.arg)

class RequitesTest(CallbackTestBase):
    def test__callback_order(self):
        self.called_first = False
        self.called_second = False
        @self.hook.register
        @requires(lambda:self.called_first)
        def second():
            self.assertTrue(self.called_first)
            self.called_second = True
        @self.hook.register
        def first():
            self.assertFalse(self.called_second)
            self.called_first = True
        self.hook()
        self.assertTrue(self.called_first)
        self.assertTrue(self.called_second)
    def test__raises_exception(self):
        @self.hook.register
        @requires(lambda:False)
        def second():
            self.fail()
        with self.assertRaises(RequirementsNotMet):
            self.hook()

class HookExceptionsTest(CallbackTestBase):
    def setUp(self):
        super(HookExceptionsTest, self).setUp()
        self.callbacks = [self.forge.create_wildcard_function_stub() for _ in range(5)]
        for index, callback in enumerate(self.callbacks):
            self.hook.register(callback)
            expected_call = callback(arg_value=self.arg)
            if index % 3 == 0:
                expected_call.and_raise(CustomException(index))
    def test_swallow_exceptions(self):
        self.override_config("hooks.swallow_exceptions", True)
        self.forge.replay()
        self.hook(arg_value=self.arg)
    def test_dont_swallow_exceptions(self):
        self.override_config("hooks.swallow_exceptions", False)
        self.forge.replay()
        with self.assertRaises(CustomException) as caught:
            self.hook(arg_value=self.arg)
        self.assertEquals(caught.exception.args[0], 0, "First exception was not the one propagated from hook!")
