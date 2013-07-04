from .utils import TestCase
from slash.result import Result
from slash.result import SessionResult

class SessionResultTest(TestCase):
    def setUp(self):
        super(SessionResultTest, self).setUp()
        results = [
            Result() for _ in range(10)
            ]
        # one result with both errors and failures
        results[1].add_error()
        results[1].add_failure()
        # one result with failure
        results[2].add_failure()
        # one result with error
        results[3].add_error()

        # one result will skip
        results[4].add_skip("Reason")

        # and one result will skip with error
        results[5].add_error()
        results[5].add_skip("Reason")
        num_finished = 7

        for result in results[:num_finished]:
            result.mark_finished()
        self.result = SessionResult(results.__iter__)
    def test_counts(self):
        self.assertEquals(self.result.get_num_successful(), 2)
        # errors take precedence over failures
        self.assertEquals(self.result.get_num_errors(), 3)
        self.assertEquals(self.result.get_num_skipped(), 2)
        self.assertEquals(self.result.get_num_failures(), 1)
