# pylint: disable-msg=W0201
from .utils.test_generator import TestGenerator
from .utils import TestCase, CustomException
import slash
from slash.runner import run_tests
from slash.exceptions import NoActiveSession
from slash import Session
from slash.core.result import Result
from slash.ctx import context
import random

class NoActiveSessionTest(TestCase):
    def test_run_tests_fails_without_active_session(self):
        with self.assertRaises(NoActiveSession):
            run_tests([])

class TestRunningTestBase(TestCase):
    def setUp(self):
        super(TestRunningTestBase, self).setUp()
        self.generator = TestGenerator()
        self.total_num_tests = 10
        self.runnables = [t.generate_test() for t in self.generator.generate_tests(self.total_num_tests)]
        self.configure()
        with Session() as session:
            self.session = session
            context.current_test_generator = self.generator
            self.prepare_runnables()
            run_tests(self.runnables)
        self.assertEquals(
            self.session.is_complete(),
            self.should_be_complete(),
            "Session unexpectedly complete" if self.session.is_complete() else "Session unexpectedly incomplete"
        )
    def prepare_runnables(self):
        pass
    def configure(self):
        pass
    def should_be_complete(self):
        return True

class AllSuccessfulTest(TestRunningTestBase):

    def test_all_executed(self):
        self.generator.assert_all_run()

    def test_iter_results_ordering(self):
        results = list(self.session.results.iter_test_results())
        for index, (result, test) in enumerate(zip(results, self.runnables)):
            self.assertIs(result.test_metadata, test.__slash__, "Test #{0} mismatch".format(index))

_RESULT_PREDICATES = set([
    getattr(Result, method_name)
    for method_name in dir(Result) if method_name.startswith("is_")
    ])

class FailedItemsTest(TestRunningTestBase):
    def prepare_runnables(self):
        num_unsuccessfull = len(self.runnables) // 2
        num_error_tests = 2
        assert 1 < num_unsuccessfull < len(self.runnables)
        unsuccessful = random.sample(self.runnables, num_unsuccessfull)
        self.error_tests = [unsuccessful.pop(-1) for _ in range(num_error_tests)]
        self.skipped_tests = [unsuccessful.pop(-1)]
        self.failed_tests = unsuccessful
        assert self.error_tests and self.failed_tests
        for failed_test in self.failed_tests:
            self.generator.make_test_fail(failed_test)
        for skipped_test in self.skipped_tests:
            self.generator.make_test_skip(skipped_test)
        for error_test in self.error_tests:
            self.generator.make_test_raise_exception(error_test)

    def test_all_executed(self):
        self.generator.assert_all_run()

    def test_failed_items_failed(self):
        self._test_results(self.failed_tests, [Result.is_finished, Result.is_failure, Result.is_just_failure])

    def test_error_items_error(self):
        self._test_results(self.error_tests, [Result.is_finished, Result.is_error])

    def test_skipped_items_skipped(self):
        self._test_results(self.skipped_tests, [Result.is_finished, Result.is_skip])

    def _test_results(self, tests, true_predicates):
        true_predicates = set(true_predicates)
        assert _RESULT_PREDICATES >= true_predicates, "{0} is not a superset of {1}".format(_RESULT_PREDICATES, true_predicates)
        for test in tests:
            result = self.session.results.get_result(test)
            for predicate in _RESULT_PREDICATES:
                predicate_result = predicate(result)
                self.assertEquals(predicate_result,
                                  predicate in true_predicates,
                                  "Predicate {0} unexpectedly returned {1}".format(predicate, predicate_result))

class StopOnFailuresTest(TestCase):

    def test_stop_on_error(self):
        self._test_stop_on_failure(error_in="test")

    def test_stop_on_error_before(self):
        self._test_stop_on_failure(error_in="before")

    def test_stop_on_error_after(self):
        self._test_stop_on_failure(error_in="after")

    _debug_called = False
    def debug_if_needed_stub(self, exc_info):
        if exc_info[0] is CustomException:
            self._debug_called = True

    def _test_stop_on_failure(self, error_in, num_tests=10):
        self.override_config("run.stop_on_error", True)
        self.override_config("debug.enabled", True)
        self.addCleanup(setattr, slash.utils.debug, "_KNOWN_DEBUGGERS", slash.utils.debug._KNOWN_DEBUGGERS)
        slash.utils.debug._KNOWN_DEBUGGERS = [self.debug_if_needed_stub]
        assert error_in in ("before", "test", "after")
        failing_index = 5
        self.current_test_index = -1
        class SampleTest(slash.Test):

            def before(self_):
                self.current_test_index += 1
                if error_in == "before" and self.current_test_index == failing_index:
                    raise CustomException()

            def after(self_):
                if error_in == "after" and self.current_test_index == failing_index:
                    raise CustomException()

            @slash.parameters.iterate(x=list(range(num_tests)))
            def test(self_, x):
                if error_in == "test" and self.current_test_index == failing_index:
                    raise CustomException()

        tests = list(SampleTest.generate_tests())

        with slash.Session() as session:
            slash.runner.run_tests(tests)

        self.assertTrue(self._debug_called)

        for index, test in enumerate(tests):
            if index <= failing_index:
                result = session.results.get_result(test)
                self.assertTrue(result.is_finished())
            else:
                with self.assertRaises(LookupError):
                    session.results.get_result(test)

### make nosetests ignore stuff we don't want to run
run_tests.__test__ = False
