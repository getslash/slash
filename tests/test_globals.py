from .utils import TestCase
import slash
from slash.session import Session
from slash import context

class GlobalsTest(TestCase):
    def setUp(self):
        super(GlobalsTest, self).setUp()
        self.session = Session()
        self.session.activate()
    def tearDown(self):
        self.session.deactivate()
        self.assertIsNone(context.session)
    def test_get_current_session(self):
        self.assertIs(context.session, self.session)
    def test_get_current_test(self):
        self.assertIsNone(context.test)
        self.assertIsNone(context.test_id)
        parent_test = self
        class Test(slash.Test):
            def test(self):
                parent_test.assertIs(context.test, self)
                parent_test.assertEquals(context.test_id, self.__slash__.id)
        slash.runner.run_tests(Test.generate_tests())
        self.assertTrue(self.session.result.is_success())
