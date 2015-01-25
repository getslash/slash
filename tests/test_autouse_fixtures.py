import pytest


def test_autouse_fixtures_global(tracked_suite):

    fixture = tracked_suite.slashconf.add_fixture(autouse=True)

    results = tracked_suite.run().session.results
    assert len(results) > 0
    for result in results:
        assert fixture.id in result.data['active_fixtures']

def test_autouse_fixtures_specific_module(tracked_suite, suite_test):

    fixture = suite_test.file.add_fixture(autouse=True)
    summary = tracked_suite.run()
    assert len(summary.session.results) > 0
    assert len(tracked_suite.files) > 1

    for test in tracked_suite:
        for result in summary.get_all_results_for_test(test):
            if test.file is suite_test.file:
                assert fixture.id in result.data['active_fixtures']
            else:
                assert fixture.id not in result.data['active_fixtures']


@pytest.fixture
def tracked_suite(suite, suite_test):
    assert len(suite)
    for test in suite:
        test.prepend_line('slash.context.result.data["active_fixtures"] = __ut__.get_fixture_memento()')
    return suite
