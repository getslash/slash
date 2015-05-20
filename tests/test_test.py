from .utils import (
    TestCase,
    CustomException,
    run_tests_in_session,
    make_runnable_tests,
    )
import itertools
import slash
from slash.loader import Loader

class TestTest(TestCase):
    """
    Test the :class:`Test` class, which is the quickest way to create test classes in Slash
    """
    def test_test_class(self):
        events = []
        class Test(slash.Test):
            def before(self):
                events.append("before")
            def after(self):
                events.append("after")
            def test_1(self):
                events.append("test_1")
            def test_2(self):
                events.append("test_2")
        with slash.Session():
            tests = make_runnable_tests(Test)
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
        class Test(slash.Test):
            def before(self):
                raise CustomException()
            def test(self):
                events.append("test")
            def after(self):
                events.append("after")
        with slash.Session():
            [test] = make_runnable_tests(Test)
        with self.assertRaises(CustomException):
            test.run()
        self.assertEquals(events, [])

    def test_after_failures(self):
        class Test(slash.Test):
            def test(self):
                assert False, "msg1"

            def after(self):
                assert False, "msg2"

        session = run_tests_in_session(Test)
        self.assertFalse(session.results.is_success())
        [result] = session.results.iter_test_results()
        self.assertEquals(len(result.get_failures()), 2)

    def test_after_gets_called(self):
        "If before() is successful, after() always gets called"
        events = []
        class Test(slash.Test):
            def before(self):
                events.append("before")
            def test_1(self):
                events.append("test")
                raise CustomException(1)
            def after(self):
                events.append("after")
        with slash.Session():
            [test] = make_runnable_tests(Test)
        with self.assertRaises(CustomException):
            test.run()
        self.assertEquals(events, ["before", "test", "after"])

class AbstractTestTest(TestCase):
    def test_abstract_tests(self):
        @slash.abstract_test_class
        class Abstract(slash.Test):
            def test1(self):
                pass
            def test2(self):
                pass
            def test3(self):
                pass
        with slash.Session():
            self.assertEquals(list(make_runnable_tests(Abstract)), [])
        class Derived(Abstract):
            pass
        with slash.Session():
            self.assertEquals(len(list(make_runnable_tests(Derived))), 3)

class TestParametersTest(TestCase):
    def test_parameters(self):
        variations = []
        a_values = [1, 2]
        b_values = [3, 4]
        c_values = [5, 6]
        d_values = [7, 8]
        class Parameterized(slash.Test):
            @slash.parameters.iterate(a=a_values)
            def before(self, a):
                variations.append([a])
            @slash.parameters.iterate(b=b_values, c=c_values)
            def test(self, b, c):
                variations[-1].extend([b, c])
            @slash.parameters.iterate(d=d_values)
            def after(self, d):
                variations[-1].append(d)
        with slash.Session():
            for test in make_runnable_tests(Parameterized):
                test.run()
        self.assertEquals(
            set(tuple(x) for x in variations),
            set(itertools.product(
                a_values,
                b_values,
                c_values,
                d_values
            )))
