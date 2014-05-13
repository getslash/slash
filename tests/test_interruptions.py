# pylint: disable-msg=W0201
import gossip
import slash
from slash import Session
from slash.runner import run_tests

from .utils import TestCase
from .utils.test_generator import TestGenerator


class InterruptionTest(TestCase):
    def setUp(self):
        super(InterruptionTest, self).setUp()
        self.generator = TestGenerator()
        self.total_num_tests = 5
        self.runnables = [t.generate_test() for t in self.generator.generate_tests(self.total_num_tests)]
        self.interrupted_index = 3
        self.interrupted = self.runnables[self.interrupted_index]
        self.generator.add_test_run_callback(self.interrupted, self._do_test_callback)
        slash.hooks.test_interrupt.register(self._test_interrupt_hook, token=id(self))
        self.addCleanup(gossip.unregister_token, id(self))

        with Session() as session:
            self.session = session
            with self.assertRaises(KeyboardInterrupt):
                run_tests(self.runnables)

    def _do_test_callback(self, _):
        slash.add_cleanup(self._regular_cleanup)
        slash.add_critical_cleanup(self._critical_cleanup)
        raise KeyboardInterrupt()

    _regular_cleanup_called = False
    def _regular_cleanup(self):
        self._regular_cleanup_called = True

    def _critical_cleanup(self):
        self._critical_cleanup_called = True

    def _test_interrupt_hook(self):
        self._hook_called_with_id = slash.context.test.TESTGENERATOR_TEST_ID

    def test_interrupted_run(self):
        for index, test in enumerate(self.runnables):
            if index > self.interrupted_index:
                with self.assertRaises(LookupError):
                    self.session.results.get_result(test)
                continue
            result = self.session.results.get_result(test)
            self.assertTrue(result.is_finished())
            if index < self.interrupted_index:
                self.assertTrue(result.is_success())
            else:
                self.assertFalse(result.is_success())

    def test_test_interrupt_hook_called(self):
        self.assertEquals(self._hook_called_with_id, self.interrupted.TESTGENERATOR_TEST_ID)

    def test_regular_cleanups_not_called(self):
        self.assertFalse(self._regular_cleanup_called)

    def test_critical_cleanups_called(self):
        self.assertTrue(self._critical_cleanup_called)



### make nosetests ignore stuff we don't want to run
run_tests.__test__ = False
