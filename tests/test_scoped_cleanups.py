import pytest

import slash

from .utils.suite_writer import Suite

_MODULE_SCOPE_ADDER = 'slash.add_cleanup({0}, scope="module")'


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
