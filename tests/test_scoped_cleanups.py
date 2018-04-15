# pylint: disable=redefined-outer-name,unused-variable,unused-argument
import pytest


import slash
from slash.loader import Loader

from .utils.suite_writer import Suite

_MODULE_SCOPE_ADDER = 'slash.add_cleanup({0}, scope="module")'


def test_cleanups_from_test_start(suite):

    num_tests = 5
    for _ in range(num_tests):
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

    @slash.hooks.register
    def before_session_cleanup():
        events.append('before_session_cleanup')

    @slash.hooks.register
    def session_start():
        slash.add_cleanup(events.append, args=(('session_cleanup', 1),))
        slash.add_cleanup(events.append, args=(('session_cleanup', 2),))

    @slash.hooks.register
    def after_session_end():
        events.append('after_session_end')

    @slash.hooks.register
    def session_end():
        events.append('session_end')

    suite.run()

    expected_session_cleanup = [
        'before_session_cleanup',
        ('session_cleanup', 2),
        ('session_cleanup', 1),
        'session_end',
        'after_session_end',
    ]
    assert len(events) - len(expected_session_cleanup) == len(suite) * 2 == num_tests * 2

    expected = []
    for test_id in test_ids:
        expected.append(('test_start', test_id))
        expected.append(('test_cleanup', test_id))
    expected.extend(expected_session_cleanup)
    assert events == expected


def test_module_scope(scoped_suite, file1_tests, file2_tests):
    file1_test = file1_tests[0]
    file1_end = file1_tests[-1].add_deferred_event(decorator='slash.add_cleanup')
    file1_test_cleanup = file1_test.add_deferred_event(adder=_MODULE_SCOPE_ADDER)

    summary = scoped_suite.run()
    assert summary.events[file1_end].timestamp < summary.events[file1_test_cleanup].timestamp



def test_cleanups_without_session_start_never_called(checkpoint):
    assert not checkpoint.called
    with slash.Session():
        slash.add_cleanup(checkpoint)
        assert not checkpoint.called
    assert not checkpoint.called


def test_cleanups_before_session_start_get_deferred(checkpoint):
    with slash.Session() as s:
        slash.add_cleanup(checkpoint)
        with s.get_started_context():
            assert not checkpoint.called
        assert checkpoint.called_count == 1


def test_cleanups_within_cleanups_preserve_scope(checkpoint1):
    """Cleanups added from within other cleanups should happen within the scope of the parent cleanups
    """

    @slash.parametrize('x', [1, 2])
    def test_something(x):
        pass

    with slash.Session() as s:
        [fake_test1, fake_test2] = Loader().get_runnables(test_something)  # pylint: disable=unbalanced-tuple-unpacking

        s.scope_manager.begin_test(fake_test1)

        def cleanup():
            slash.add_cleanup(checkpoint1)

        slash.add_cleanup(cleanup)

        assert not checkpoint1.called
        s.scope_manager.end_test(fake_test1)

        assert checkpoint1.called


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
