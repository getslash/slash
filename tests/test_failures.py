import slash
from .utils import TestCase

class FailuresAndErrorsTest(TestCase):

    def test_adding_errors_global(self):
        self._test_adding_errors_failures_strings(
            slash.add_error,
            lambda result: result.get_errors(),
            False,
        )

    def test_adding_errors_in_test(self):
        self._test_adding_errors_failures_strings(
            slash.add_error,
            lambda result: result.get_errors(),
            True,
        )

    def test_adding_failures_global(self):
        self._test_adding_errors_failures_strings(
            slash.add_failure,
            lambda result: result.get_failures(),
            False,
        )

    def test_adding_failures_in_test(self):
        self._test_adding_errors_failures_strings(
            slash.add_failure,
            lambda result: result.get_failures(),
            True
        )

    def _test_adding_errors_failures_strings(self, adder, getter, in_specific_test):
        obj = SampleObject()
        class Test(slash.Test):
            def test(self):
                adder("msg1")
                adder("msg2")
                adder(obj)


        with slash.Session() as session:
            if in_specific_test:
                slash.run_tests(slash.loader.Loader().iter_test_factory(Test))
                [result] = session.results.iter_test_results()
            else:
                list(Test.generate_tests())[0].run()
                result = session.results.global_result

        self.assertFalse(result.is_success())

        [error1, error2, error3] = getter(result)
        self.assertEquals(error1.message, "msg1")
        self.assertEquals(error2.message, "msg2")
        self.assertEquals(error3.message, None)
        self.assertIs(error3.arg, obj)

class SampleObject(object):
    pass
