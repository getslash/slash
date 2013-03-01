# pylint: disable-msg=W0201
from .utils.test_generator import TestGenerator
from shakedown.runner import run_tests
from shakedown.session import Session
from shakedown.suite import Suite
from shakedown.ctx import context
import six # pylint: disable=F0401
import random
from .utils import TestCase

class TestRunningTestBase(TestCase):
    def setUp(self):
        super(TestRunningTestBase, self).setUp()
        self.generator = TestGenerator()
        self.runnables = [t.generate_test() for t in self.generator.generate_tests(7)]
        with Session() as session:
            self.session = session
            with Suite() as suite:
                context.current_test_generator = self.generator
                self.suite = suite
                self.prepare_runnables()
                run_tests(self.runnables)
    def prepare_runnables(self):
        pass

class AllSuccessfulTest(TestRunningTestBase):
    def test__all_executed(self):
        self.generator.assert_all_run()

class FailedItemsTest(TestRunningTestBase):
    def prepare_runnables(self):
        num_unsuccessfull = len(self.runnables) // 2
        num_error_tests = 2
        assert 1 < num_unsuccessfull < len(self.runnables)
        unsuccessful = random.sample(self.runnables, num_unsuccessfull)
        self.error_tests = [unsuccessful.pop(-1) for _ in six.moves.xrange(num_error_tests)]
        self.failed_tests = unsuccessful
        assert self.error_tests and self.failed_tests
        for failed_test in self.failed_tests:
            self.generator.make_test_fail(failed_test)
        for error_test in self.error_tests:
            self.generator.make_test_raise_exception(error_test)
    def test__all_executed(self):
        self.generator.assert_all_run()
    def test__failed_items_failed(self):
        for failed_test in self.failed_tests:
            result = self.suite.get_result(failed_test)
            self.assertTrue(result.is_failure())
            self.assertFalse(result.is_error())
            self.assertFalse(result.is_success())
    def test__error_items_error(self):
        for error_test in self.error_tests:
            result = self.suite.get_result(error_test)
            self.assertTrue(result.is_error())
            self.assertFalse(result.is_failure())
            self.assertFalse(result.is_success())

### make nosetests ignore stuff we don't want to run
run_tests.__test__ = False
