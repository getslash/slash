import pytest



import slash

from .utils.suite_writer import Suite

_MODULE_SCOPE_ADDER = 'slash.add_cleanup({0}, scope="module")'


def test_cleanups_from_test_start(suite):

    num_tests = 5
    for i in range(num_tests):
        suite.add_test()

    events = []
    test_ids = []

    @slash.hooks.register
    def test_start():
        test_id = slash.context.test.__slash__.id
        test_ids.append(test_id)
        events.append(('test_start', test_id))
        @slash.add_cleanup
        def cleanup():
            events.append(('test_cleanup', test_id))

    suite.run()

    assert len(events) == len(suite) * 2 == num_tests * 2
    expected = []
    for test_id in test_ids:
        expected.append(('test_start', test_id))
        expected.append(('test_cleanup', test_id))
    assert events == expected


def test_module_scope(scoped_suite, file1_tests, file2_tests):
    file1_test = file1_tests[0]
    file1_end = file1_tests[-1].add_deferred_event(decorator='slash.add_cleanup')
    file1_test_cleanup = file1_test.add_deferred_event(adder=_MODULE_SCOPE_ADDER)

    summary = scoped_suite.run()
    assert summary.events[file1_end].timestamp < summary.events[file1_test_cleanup].timestamp


def test_test_scoped_cleanups_in_session(checkpoint):
    # with scoped cleanups, and the default being 'test', there is a special meaning
    # for cleanups registered outside of tests....
    with slash.Session() as s:
        slash.add_cleanup(checkpoint)
        assert not checkpoint.called
        with s.get_started_context():
            pass

        assert not checkpoint.called
    assert checkpoint.called


def test_errors_associated_with_correct_result(scoped_suite, file1_tests, file2_tests):
    file1_test = file1_tests[0]
    file1_test_cleanup = file1_test.add_deferred_event(adder=_MODULE_SCOPE_ADDER, extra_code=['assert 1 == 2'])
    file1_test.expect_failure()

    scoped_suite.run()


@pytest.fixture
def scoped_suite(suite, file1_tests, file2_tests):
    return suite

@pytest.fixture
def suite():
    return Suite()


@pytest.fixture
def file1_tests(suite):
    file1 = suite.add_file()
    return [file1.add_function_test() for i in range(5)]

@pytest.fixture
def file2_tests(suite):
    file2 = suite.add_file()
    return [file2.add_function_test() for i in range(3)]
