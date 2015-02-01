import pytest

from .utils.suite_writer import Suite


def test_run_suite_normal(suite):
    result = suite.run()
    assert result.session.results.get_num_successful() == len(suite)


def test_suite_events(suite):
    test1, test2 = suite[2], suite[3]
    result = suite.run()
    assert result.events['test_start', test1.id].is_before(result.events['test_start', test2.id])





@pytest.fixture
def suite():
    s = Suite()
    for i in range(10):
        s.add_test()
    return s
