import slash

from .utils import run_tests_assert_success, TestCase


class WarningsTest(TestCase):

    def setUp(self):
        super(WarningsTest, self).setUp()

        class SampleTest(slash.Test):
            def test(self):
                slash.logger.warning("this is a warning")

        self.session = run_tests_assert_success(SampleTest)

    def test_session_warnings(self):
        self.assertEquals(len(self.session.warnings), 1)
        [warning] = self.session.warnings
