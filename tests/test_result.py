from .utils import TestCase
from slash._compat import OrderedDict
from slash.core.result import Result
from slash.core.result import SessionResults

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
        self.result = SessionResults()
        for index, r in enumerate(self.results):
            self.result._results_dict[index] = r

    def test_counts(self):
        self.assertEquals(self.result.get_num_results(), len(self.results))
        self.assertEquals(self.result.get_num_successful(), 2)
        # errors take precedence over failures
        self.assertEquals(self.result.get_num_errors(), 3)
        self.assertEquals(self.result.get_num_skipped(), 2)
        self.assertEquals(self.result.get_num_failures(), 1)
