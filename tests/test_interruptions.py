# pylint: disable-msg=W0201
from .utils.test_generator import TestGenerator
from slash.runner import run_tests
from slash.session import Session
from slash.result import Result
import slash
from .utils import TestCase

class InterruptionTest(TestCase):
    def setUp(self):
        super(InterruptionTest, self).setUp()
        self.generator = TestGenerator()
        self.total_num_tests = 5
        self.runnables = [t.generate_test() for t in self.generator.generate_tests(self.total_num_tests)]
        self.interrupted_index = 3
        self.interrupted = self.runnables[self.interrupted_index]
        self.generator.add_test_run_callback(self.interrupted, self._do_interrupt)
        slash.hooks.test_interrupt.register(self._test_interrupt_hook, id(self))
        self.addCleanup(slash.hooks.test_interrupt.unregister_by_identifier, id(self))

        with Session() as session:
            self.session = session
            with self.assertRaises(KeyboardInterrupt):
                run_tests(self.runnables)

    def _do_interrupt(self, _):
        raise KeyboardInterrupt()

    def _test_interrupt_hook(self):
        self._hook_called_with_id = slash.context.test.TESTGENERATOR_TEST_ID

    def test_interrupted_run(self):
        for index, test in enumerate(self.runnables):
            if index > self.interrupted_index:
                with self.assertRaises(LookupError):
                    self.session.get_result(test)
                continue
            result = self.session.get_result(test)
            self.assertTrue(result.is_finished())
            if index < self.interrupted_index:
                self.assertTrue(result.is_success())
            else:
                self.assertFalse(result.is_success())

    def test_test_interrupt_hook_called(self):
        self.assertEquals(self._hook_called_with_id, self.interrupted.TESTGENERATOR_TEST_ID)


### make nosetests ignore stuff we don't want to run
run_tests.__test__ = False
