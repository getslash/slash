import pytest


@pytest.mark.parametrize("scope", ["module", "test"])
@pytest.mark.parametrize("error_adder", [None, "add_error", "add_failure"])
def test_fixture_start_end_test(suite, suite_test, scope, error_adder):

    fixture = suite.slashconf.add_fixture(scope=scope)

    start_event = fixture.add_deferred_event(
        "this.test_start", name="fixture_test_start"
    )
    end_event = fixture.add_deferred_event("this.test_end", name="fixture_test_end")
    test_event = suite_test.add_event()

    suite_test.depend_on_fixture(fixture)

    if error_adder == "add_error":
        suite_test.when_run.error()
    elif error_adder == "add_failure":
        suite_test.when_run.fail()
    else:
        assert error_adder is None

    events = suite.run().events

    if scope != "module":
        # for module scope, the event will get run over, resulting in later `test_start` events...
        assert events[start_event].timestamp < events[test_event].timestamp
    assert events[end_event].timestamp > events[test_event].timestamp


def test_fixture_end_test_raises_excepiton(suite_builder):
    @suite_builder.first_file.add_code
    def __code__():
        # pylint: disable=unused-variable
        import slash  # pylint: disable=redefined-outer-name, reimported

        @slash.fixture
        @slash.parametrize("param", [1, 2])
        def fixture(this, param):
            @this.test_end
            def test_end(*_, **__):
                1 / 0  # pylint: disable=pointless-statement

            return param

        def test_something(fixture):
            slash.context.result.data["value"] = fixture

    suite_builder.build().run().assert_all(2).exception(ZeroDivisionError).with_data(
        [{"value": 1}, {"value": 2}]
    )
