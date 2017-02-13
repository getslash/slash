# pylint: disable=redefined-outer-name
import pytest

from .utils.suite_writer import Suite
from .utils.suite_writer.slash_run_result import Events


def test_run_suite_normal(suite):
    result = suite.run()
    assert result.session.results.get_num_successful() == len(suite)


def test_suite_events(suite):
    test1, test2 = suite[2], suite[3]
    result = suite.run()
    assert result.events['test_start', test1.id].is_before(result.events['test_start', test2.id])


def test_events_non_tuple():
    events = Events()
    events.add('a')
    assert 'a' in events
    assert 'b' not in events
    assert events.has_event('a')
    assert not events.has_event('b')


def test_events_tuple():
    events = Events()
    events.add('a', 'b', 'c')
    assert 'a' not in events
    assert 'b' not in events
    assert ('a', 'b', 'c') in events
    assert ('a',) not in events
    assert events.has_event('a', 'b', 'c')
    assert not events.has_event('a')





@pytest.fixture
def suite():
    s = Suite()
    for _ in range(10):
        s.add_test()
    return s
