import gc

import pytest
import slash
from slash import Session
from slash.core.result import Result, SessionResults

from .utils import TestCase, run_tests_assert_success


@pytest.mark.parametrize('use_error', [True, False])
def test_result_add_exception_multiple_times(result, use_error):
    with slash.Session():
        second_result = type(result)()
        second_result.mark_started()
        try:
            if use_error:
                1 / 0               # pylint: disable=pointless-statement
            else:
                assert 1 + 1 == 3
        except:
            for _ in range(3):
                result.add_exception()
            second_result.add_exception()

    assert result.is_error() == use_error
    assert result.is_failure() == (not use_error)
    assert len(result.get_errors()
               if use_error else result.get_failures()) == 1
    assert second_result.is_success()


def test_result_summary_some_not_run(suite):
    suite[2].add_decorator('slash.requires(False)')
    suite[2].expect_skip()
    results = suite.run().session.results
    assert results.is_success(allow_skips=True)


def test_get_num_skips_no_not_run(suite, suite_test):
    suite_test.add_decorator('slash.requires(False)')
    suite_test.expect_skip()
    results = suite.run().session.results
    assert results.get_num_skipped(include_not_run=False) == 0
    assert results.get_num_skipped(include_not_run=True) == 1
    assert results.get_num_skipped() == 1


def test_result_summary(suite):

    suite[2].when_run.fail()
    suite[3].when_run.raise_exception()
    suite[4].when_run.raise_exception()
    suite[5].when_run.skip()

    results = suite.run().session.results

    assert results.get_num_errors() == 2
    assert results.get_num_failures() == 1
    assert results.get_num_skipped() == 1
    assert results.get_num_successful() == len(suite) - 4
    assert results.get_num_not_run() == 0


def test_result_not_run(suite, suite_test, is_last_test):
    suite_test.when_run.fail()

    for test in suite.iter_all_after(suite_test, assert_has_more=not is_last_test):
        test.expect_not_run()

    summary = suite.run(additional_args=['-x'])

    num_not_run = summary.session.results.get_num_not_run()
    if is_last_test:
        assert num_not_run == 0
    else:
        assert 0 < num_not_run < len(suite)


def test_result_not_run_zero_when_all_success(suite):
    summary = suite.run()
    assert summary.session.results.get_num_not_run() == 0


def test_has_errors_or_failures(suite):
    suite[2].when_run.fail()
    suite[3].when_run.raise_exception()
    results = suite.run().session.results
    assert not results[0].has_errors_or_failures()
    assert results[2].has_errors_or_failures()
    assert results[3].has_errors_or_failures()


def test_has_skips(suite):
    suite[1].when_run.skip()
    results = suite.run().session.results
    assert not results[0].has_skips()
    assert results[1].has_skips()


def test_result_data_is_unique():

    class SampleTest(slash.Test):

        def test_1(self):
            pass

        def test_2(self):
            pass

    session = run_tests_assert_success(SampleTest)
    [result1, result2] = session.results
    assert result1.data is not result2.data


def test_result_test_garbage_collected(gc_marker):

    class SomeTest(slash.Test):

        def test_something(self):
            pass

    # we have to run another test at the end to make sure Slash's internal _last_test
    # doesn't refer to our test
    class OtherTest(slash.Test):

        def test_something(self):
            pass

    with slash.Session() as s:
        loader = slash.loader.Loader()
        tests = loader.get_runnables(SomeTest)
        # we use list(genexp) to prevent 't' from leaking
        marks = list(gc_marker.mark(t) for t in tests)
        session = run_tests_assert_success(
            tests + loader.get_runnables(OtherTest))
        del tests
    gc.collect()
    for mark in marks:
        assert mark.destroyed


def test_add_error_traceback_for_manually_added_errors(suite, suite_test):
    suite_test.append_line('slash.add_error("msg")')
    suite_test.expect_error()

    [result] = suite.run().get_all_results_for_test(suite_test)
    [err] = result.get_errors()
    assert err.traceback


class SessionResultTest(TestCase):

    def setUp(self):
        super(SessionResultTest, self).setUp()
        self.results = [
            Result() for _ in range(10)
        ]
        for r in self.results:
            r.mark_started()
        # one result with both errors and failures
        try:
            1 / 0
        except:
            self.results[1].add_error()
            self.results[1].add_failure()
            # one result with failure
            self.results[2].add_failure()
            # one result with error
            self.results[3].add_error()
            self.results[5].add_error()

        # one result will skip
        self.results[4].add_skip("Reason")

        # and one result will skip with error
        self.results[5].add_skip("Reason")
        num_finished = 7

        for result in self.results[:num_finished]:
            result.mark_finished()
        self.result = SessionResults(Session())
        for index, r in enumerate(self.results):
            self.result._results_dict[index] = r

    def test_counts(self):
        self.assertEquals(self.result.get_num_results(), len(self.results))
        self.assertEquals(self.result.get_num_successful(), 2)
        # errors take precedence over failures
        self.assertEquals(self.result.get_num_errors(), 3)
        self.assertEquals(self.result.get_num_skipped(), 2)
        self.assertEquals(self.result.get_num_failures(), 1)
