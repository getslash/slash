from .utils import TestCase
import slash

class SkipTestTest(TestCase):
    def test_skip_test(self):
        "Make sure the skip_test function raises a SkipTest exception"
        for args in [
                (), ("message",)
        ]:
            with self.assertRaises(slash.exceptions.SkipTest) as caught:
                slash.skip_test(*args)
            if args:
                self.assertEquals(caught.exception.reason, args[0])

class SkipWithBeforeAfterTest(TestCase):
    def test(self):
        "Make sure that after() is called for Test even if we skip"
        parent_test = self
        class MyTest(slash.Test):
            def test(self):
                slash.skip_test("!")
            def after(self):
                parent_test.after_called = True
        [test] = MyTest.generate_tests()
        with self.assertRaises(slash.exceptions.SkipTest):
            test.run()
        self.assertTrue(self.after_called, "after() was not called upon skip")

class SkipDecoratorTest(TestCase):
    def test_method_without_reason(self):
        class Test(slash.Test):
            @slash.skipped
            def test(self):
                pass
        [test] = Test.generate_tests()
        self.assert_skips(test.run)
    def test_method_with_reason(self):
        class Test(slash.Test):
            @slash.skipped("reason")
            def test(self):
                pass
        [test] = Test.generate_tests()
        self.assert_skips(test.run, "reason")
    def test_class_decorator(self):
        @slash.skipped("reason")
        class Test(slash.Test):
            def test_1(self):
                pass
            def test_2(self):
                pass

        [test_1, test_2] = Test.generate_tests()

        self.assert_skips(test_1.run, "reason")
        self.assert_skips(test_2.run, "reason")
    def assert_skips(self, thing, reason=None):
        with self.assertRaises(slash.exceptions.SkipTest) as caught:
            thing()
        self.assertEquals(caught.exception.reason, reason)
