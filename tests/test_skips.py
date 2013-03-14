from .utils import TestCase
import shakedown

class SkipTestTest(TestCase):
    def test__skip_test(self):
        "Make sure the skip_test function raises a SkipTest exception"
        for args in [
                (), ("message",)
        ]:
            with self.assertRaises(shakedown.exceptions.SkipTest) as caught:
                shakedown.skip_test(*args)
            if args:
                self.assertEquals(caught.exception.reason, args[0])

class SkipWithBeforeAfterTest(TestCase):
    def test(self):
        "Make sure that after() is called for Test even if we skip"
        parent_test = self
        class MyTest(shakedown.Test):
            def test(self):
                shakedown.skip_test("!")
            def after(self):
                parent_test.after_called = True
        [test] = MyTest.generate_tests()
        with self.assertRaises(shakedown.exceptions.SkipTest):
            test.run()
        self.assertTrue(self.after_called, "after() was not called upon skip")
