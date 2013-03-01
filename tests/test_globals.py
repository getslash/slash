from .utils import TestCase
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
    def test__get_current_session(self):
        self.assertIs(context.session, self.session)
    def test__get_current_suite(self):
        self.assertIs(context.suite, self.suite)
