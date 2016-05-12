def test_generator_fixture(suite, suite_test, get_fixture_location):
    fixture = get_fixture_location(suite_test).add_generator_fixture()
    suite_test.depend_on_fixture(fixture)
    suite.run()
