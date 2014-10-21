from uuid import uuid1

import pytest
import slash

from .utils import run_tests_in_session


def test_fixture_cleanup(populated_suite, suite_test):
    fixture = populated_suite.add_fixture()
    for i in range(3):
        fixture.add_cleanup()
    suite_test.add_fixture(fixture)
    populated_suite.run()


@pytest.mark.parametrize('scope', ['session', 'module'])
def test_fixture_autouse_with_scoping(populated_suite, suite_test, scope):

    fixture = suite_test.file.add_fixture(autouse=True, scope=scope)
    fixture.add_cleanup()

    session = populated_suite.run()
