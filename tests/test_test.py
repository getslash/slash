from .utils import TestCase
import shakedown

class TestTest(TestCase):
    """
    Test the :class:`Test` class, which is the quickest way to create test classes in Shakedown
    """
    def test_test_class(self):
        events = []
        class Test(shakedown.Test):
            def before(self):
                events.append("before")
            def after(self):
                events.append("after")
            def test_1(self):
                events.append("test_1")
            def test_2(self):
                events.append("test_2")
        tests = Test.generate_tests()
        for test in tests:
            self.assertIsInstance(test, Test)
        self.assertEquals(len(tests), 2)
        tests.sort(key=lambda test: test._test_method_name)
        for test in tests:
            test.run()
        self.assertEquals(events, ["before", "test_1", "after", "before", "test_2", "after"])
    def test_before_failures(self):
        "Check that exceptions during before() prevent after() from happening"
        events = []
        class Test(shakedown.Test):
            def before(self):
                raise CustomException()
            def test(self):
                events.append("test")
            def after(self):
                events.append("after")
        [test] = Test.generate_tests()
        with self.assertRaises(CustomException):
            test.run()
        self.assertEquals(events, [])
    def test_after_gets_called(self):
        "If before() is successful, after() always gets called"
        events = []
        class Test(shakedown.Test):
            def before(self):
                events.append("before")
            def test_1(self):
                events.append("test")
                raise CustomException(1)
            def after(self):
                events.append("after")
        [test] = Test.generate_tests()
        with self.assertRaises(CustomException):
            test.run()
        self.assertEquals(events, ["before", "test", "after"])

class CustomException(Exception):
    pass
