import slash
import pytest

from .utils import TestCase
from slash import Session
from slash.core.result import Result
from slash.core.result import SessionResults, GlobalResult

from .utils import run_tests_assert_success


@pytest.mark.parametrize('use_error', [True, False])
def test_result_add_exception_multiple_times(result, use_error):
    second_result = type(result)()
    try:
        if use_error:
            1 / 0
        else:
            assert 1 + 1 == 3
    except:
        for i in range(3):
            result.add_exception()
        second_result.add_exception()

    assert result.is_error() == use_error
    assert result.is_failure() == (not use_error)
    assert len(result.get_errors() if use_error else result.get_failures()) == 1
    assert second_result.is_success()


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


class SessionResultTest(TestCase):

    def setUp(self):
        super(SessionResultTest, self).setUp()
        self.results = [
            Result() for _ in range(10)
        ]
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


@pytest.fixture(params=[GlobalResult, Result])
def result(request):
    return request.param()
