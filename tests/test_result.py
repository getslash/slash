from .utils import TestCase
from shakedown.result import Result
from shakedown.result import AggregatedResult

class AggregatedResultTest(TestCase):
    def setUp(self):
        super(AggregatedResultTest, self).setUp()
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

        # first 5 results are finished
        for result in results[:5]:
            result.mark_finished()
        self.result = AggregatedResult(results.__iter__)
    def test__counts(self):
        self.assertEquals(self.result.get_num_successful(), 2)
        # errors take precedence over failures
        self.assertEquals(self.result.get_num_errors(), 2)
        self.assertEquals(self.result.get_num_failures(), 1)
