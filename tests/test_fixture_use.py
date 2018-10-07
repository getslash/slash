def test_basic_use_fixtures(suite, suite_test):
    fixtures_names = []
    events_added = []
    for _ in range(3):
        fixture = suite_test.file.add_fixture()
        events_added.append(fixture.add_event())
        fixtures_names.append(fixture.name)
    suite_test.add_decorator('slash.use_fixtures({})'.format(fixtures_names))
    events_happened = suite.run().events
    for event in events_added:
        assert event in events_happened

def test_nested_fixtures(suite, suite_test):
    nested_fixture = suite_test.file.add_fixture()
    fixture = suite_test.file.add_fixture()
    fixture.depend_on_fixture(nested_fixture)
    suite_test.add_decorator('slash.use_fixtures({})'.format([fixture.name]))
    suite.run()

def test_use_fixture_with_string_raises(suite, suite_test):
    suite_test.add_decorator('slash.use_fixtures("example_str")')
    for test in suite:
        test.expect_deselect()
    suite.run(expect_session_errors=True)

def test_extending(suite, suite_test):
    fixture1, fixture2 = suite_test.file.add_fixture(), suite_test.file.add_fixture()
    event1, event2 = fixture1.add_event(), fixture2.add_event()
    suite_test.add_decorator('slash.use_fixtures(["{}"])'.format(fixture1.name))
    suite_test.add_decorator('slash.use_fixtures(["{}"])'.format(fixture2.name))
    events_happened = suite.run().events
    for event in [event1, event2]:
        assert event in events_happened

def test_fixture_cleanup(suite_builder):
    @suite_builder.first_file.add_code
    def __code__():  # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported
        @slash.fixture()
        def fixture_1(): # pylint: disable=unused-variable
            yield
            slash.context.result.data['params'] = 'bla'

        @slash.use_fixtures(["fixture_1"])
        def test_1(): # pylint: disable=unused-variable
            pass

    suite_builder.build().run().assert_success(1).with_data([{'params': 'bla'}])

def test_use_fixture_and_depend_on_it_called_once(suite_builder):
    @suite_builder.first_file.add_code
    def __code__():  # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name, reimported
        @slash.fixture()
        def fixture_1(): # pylint: disable=unused-variable
            if 'called_count' in slash.context.result.data:
                slash.context.result.data['called_count'] += 1
            else:
                slash.context.result.data['called_count'] = 1

        @slash.use_fixtures(["fixture_1"])
        def test_1(fixture_1): # pylint: disable=unused-variable, unused-argument
            pass

    suite_builder.build().run().assert_success(1).with_data([{'called_count': 1}])
