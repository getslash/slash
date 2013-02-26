# pylint: disable-msg=W0201
from .utils import TestBucket
from shakedown.runner import run_tests
from shakedown.session import Session
from shakedown.suite import Suite
from six.moves import xrange # pylint: disable=W0622
import random
from .utils import TestCase

class TestRunningTestBase(TestCase):
    def setUp(self):
        self.bucket = TestBucket()
        self.runnables = self.bucket.generate_tests(7)
        with Session() as session:
            self.session = session
            with Suite() as suite:
                self.suite = suite
                self.prepare_runnables()
                run_tests(self.runnables)
    def prepare_runnables(self):
        pass

class AllSuccessfulTest(TestRunningTestBase):
    def test__all_executed(self):
        self.bucket.assert_all_run()

class FailedItemsTest(TestRunningTestBase):
    def prepare_runnables(self):
        num_unsuccessfull = len(self.runnables) // 2
        num_error_tests = 2
        assert 1 < num_unsuccessfull < len(self.runnables)
        unsuccessful = random.sample(self.runnables, num_unsuccessfull)
        self.error_tests = [unsuccessful.pop(-1) for _ in xrange(num_error_tests)]
        self.failed_tests = unsuccessful
        assert self.error_tests and self.failed_tests
        for failed_test in self.failed_tests:
            self.bucket.make_test_fail(failed_test)
        for error_test in self.error_tests:
            self.bucket.make_test_raise_exception(error_test)
    def test__all_executed(self):
        self.bucket.assert_all_run()
    def test__failed_items_failed(self):
        self.skipTest("")

### make nosetests ignore stuff we don't want to run
run_tests.__test__ = False
