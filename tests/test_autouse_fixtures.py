
def test_autouse_fixtures_global(populated_suite):

    fixture = populated_suite.add_fixture(autouse=True)
    results = populated_suite.run().session.results
    assert len(results) > 0
    for result in results:
        assert fixture.uuid in result.data['active_fixture_uuid_snapshot']

def test_autouse_fixtures_specific_module(populated_suite, suite_test):

    fixture = suite_test.file.add_fixture(autouse=True)
    results = populated_suite.run().session.results
    assert len(results) > 0
    assert len(populated_suite.files) > 1
    assert not all(fixture.uuid in result.data['active_fixture_uuid_snapshot'] for result in results)
