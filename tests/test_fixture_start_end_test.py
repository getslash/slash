import pytest

@pytest.mark.parametrize('scope', ['module', 'test'])
def test_fixture_start_end_test(suite, suite_test, scope):

    fixture = suite.slashconf.add_fixture(scope=scope)

    start_event = fixture.add_deferred_event('this.test_start')
    end_event = fixture.add_deferred_event('this.test_end')
    test_event = suite_test.add_event()

    suite_test.depend_on_fixture(fixture)
    events = suite.run().events

    if scope != 'module':
        # for module scope, the event will get run over, resulting in later `test_start` events...
        assert events[start_event].timestamp < events[test_event].timestamp
    assert events[end_event].timestamp > events[test_event].timestamp
