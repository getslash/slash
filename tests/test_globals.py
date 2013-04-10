from .utils import TestCase
import shakedown
from shakedown.session import Session
from shakedown.suite import Suite
from shakedown import context

class GlobalsTest(TestCase):
    def setUp(self):
        super(GlobalsTest, self).setUp()
        self.session = Session()
        self.session.activate()
        self.suite = Suite()
        self.suite.activate()
    def tearDown(self):
        self.suite.deactivate()
        self.assertIsNone(context.suite)
        self.session.deactivate()
        self.assertIsNone(context.session)
    def test_get_current_session(self):
        self.assertIs(context.session, self.session)
    def test_get_current_suite(self):
        self.assertIs(context.suite, self.suite)
    def test_get_current_test(self):
        self.assertIsNone(context.test)
        self.assertIsNone(context.test_id)
        parent_test = self
        class Test(shakedown.Test):
            def test(self):
                parent_test.assertIs(context.test, self)
                parent_test.assertEquals(context.test_id, self.__shakedown__.id)
        shakedown.runner.run_tests(Test.generate_tests())
        self.assertTrue(self.session.result.is_success())
