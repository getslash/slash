from .utils.suite_writer import Suite

from contextlib import contextmanager

import pytest

# pylint: disable=redefined-outer-name


def test_expect_failure_not_met(suite, test):
    test.expect_failure()
    with _raises_assertion('Test did not fail as expected'):
        suite.run()

def test_expect_error_not_met(suite, test):
    test.expect_error()
    with _raises_assertion('Test did not issue error as expected'):
        suite.run()



@contextmanager
def _raises_assertion(msg):
    with pytest.raises(AssertionError) as caught:
        yield
    assert str(caught.value) == msg

@pytest.fixture
def test(suite):
    return suite[len(suite) // 2]

@pytest.fixture
def suite():
    s = Suite()
    for _ in range(10):
        s.add_test()
    return s
