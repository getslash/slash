from .utils import TestCase
import slash
from slash import Session
from slash import context

class GlobalsTest(TestCase):

    def setUp(self):
        super(GlobalsTest, self).setUp()
        self.session = Session()

    def test_get_current_session(self):
        with self.session:
            self.assertIs(context.session, self.session)
            self.assertIsNot(context.session, slash.session)
            self.assertEquals(self.session, slash.session)

    def test_get_current_test(self):
        filename = _without_pyc(__file__)
        factory_name = 'InnerTest'
        with self.session:
            self.assertIsNone(context.test)
            self.assertIsNone(context.test_id)
            parent_test = self
            class InnerTest(slash.Test):
                def test_method(self):
                    # slash.test is a proxy for the current test
                    parent_test.assertIsNot(slash.test, self)
                    parent_test.assertIs(slash.test.__slash__, self.__slash__)
                    parent_test.assertIs(context.test, self)
                    parent_test.assertEquals(context.test_id, self.__slash__.id)
                    parent_test.assertEquals(context.test_filename, _without_pyc(__file__))
            with self.session.get_started_context():
                slash.runner.run_tests(InnerTest.generate_tests(filename, factory_name))
        self.assertTrue(self.session.results.is_success())

def _without_pyc(path):
    if path.endswith(".pyc"):
        path = path[:-1]
    return path
