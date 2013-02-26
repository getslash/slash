import unittest
from shakedown.session import Session
from shakedown.suite import Suite
from shakedown.runner import run_tests
from .utils import TestBucket

class TestRunningTest(unittest.TestCase):
    def setUp(self):
        super(TestRunningTest, self).setUp()
        self.bucket = TestBucket()
        self.runnables = self.bucket.generate_tests()
        with Session() as session:
            self.session = session
            with Suite() as suite:
                self.suite = suite
                run_tests(self.runnables)
    def test__all_executed(self):
        self.bucket.assert_all_run()

### make nosetests ignore stuff we don't want to run
run_tests.__test__ = False
