from .utils import TestCase
from shakedown.session import Session
from shakedown.suite import Suite
from shakedown.ctx import ctx

class GlobalsTest(TestCase):
    def setUp(self):
        super(GlobalsTest, self).setUp()
        self.session = Session()
        self.session.activate()
        self.suite = Suite()
        self.suite.activate()
    def tearDown(self):
        self.suite.deactivate()
        self.assertIsNone(ctx.suite)
        self.session.deactivate()
        self.assertIsNone(ctx.session)
    def test__get_current_session(self):
        self.assertIs(ctx.session, self.session)
    def test__get_current_suite(self):
        self.assertIs(ctx.suite, self.suite)
