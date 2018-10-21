# pylint: disable=unused-argument,unused-variable
import gossip
import pytest
import slash
import slash.runner
from slash.exceptions import CannotAddCleanup, IncorrectScope


def test_session_cleanup(suite, suite_test):

    @suite.slashconf.append_body
    def __code__():
        @slash.add_cleanup
        def session_cleanup():
            1 / 0 # pylint: disable=pointless-statement

    summary = suite.run(expect_session_errors=True)
    assert not summary.session.results.is_success()
    [err] = summary.session.results.global_result.get_errors()
    assert err.exception_type is ZeroDivisionError
    assert 'Session error' in summary.get_console_output()


def test_cleanups_within_cleanups(suite, suite_test):

    @suite_test.append_body
    def __code__():
        @slash.add_cleanup
        def cleanup1():
            slash.context.result.data['cleanup1'] = True

            @slash.add_cleanup
            def cleanup2():
                slash.context.result.data['cleanup2'] = True

    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    assert result.data['cleanup1']
    assert result.data['cleanup2']


@pytest.mark.parametrize('other_error', ['error', 'failure', None])
def test_success_only_cleanups_with_skips(suite, suite_test, other_error):

    if other_error == 'error':
        suite_test.append_line('slash.add_error("error")')
        suite_test.expect_error()
    elif other_error == 'failure':
        suite_test.append_line('slash.add_failure("failure")')
        suite_test.expect_failure()
    elif other_error is not None:
        raise NotImplementedError()  # pragma: no cover

    @suite_test.append_body
    def __code__():
        def callback():
            __ut__.events.add('success_only_cleanup_called') # pylint: disable=undefined-variable
        slash.add_cleanup(callback, success_only=True)
        slash.skip_test()

    if other_error is None:
        suite_test.expect_skip()

    summary = suite.run()
    [result] = summary.get_all_results_for_test(suite_test)
    assert result.has_skips()
    assert ('success_only_cleanup_called' in summary.events) == (other_error is None)


def test_fatal_exceptions_from_cleanup(suite, suite_test, is_last_test):

    @suite_test.append_body
    def __code__():
        @slash.add_cleanup
        def cleanup():
            from slash.exception_handling import mark_exception_fatal
            raise mark_exception_fatal(Exception())

    suite_test.expect_error()

    for t in suite.iter_all_after(suite_test, assert_has_more=not is_last_test):
        t.expect_not_run()

    suite.run()


def test_add_skip_from_test_cleanup(suite, suite_test):
    cleanup = suite_test.add_deferred_event(decorator='slash.add_cleanup', extra_code=['slash.skip_test()'])
    suite_test.expect_skip()
    summary = suite.run()
    assert summary.events[cleanup].timestamp


@pytest.mark.parametrize('cleanup_mechanism', ['this', 'slash'])
def test_add_skip_from_fixture_cleanup(suite, suite_test, cleanup_mechanism):
    suite_test.expect_skip()
    fixture = suite.slashconf.add_fixture()
    suite_test.depend_on_fixture(fixture)
    cleanup = fixture.add_deferred_event(decorator='{}.add_cleanup'.format(cleanup_mechanism), extra_code=['slash.skip_test()'])
    summary = suite.run()
    assert summary.events[cleanup].timestamp


def test_test_cleanups_happen_before_fixture_cleanups(suite, suite_test):
    fixture = suite.slashconf.add_fixture()
    suite_test.depend_on_fixture(fixture)
    fixture_cleanup = fixture.add_cleanup()
    test_cleanup = suite_test.add_cleanup()
    events = suite.run().events

    assert events[fixture_cleanup].timestamp > events[test_cleanup].timestamp


def test_cannot_add_cleanup_without_active_session():
    with pytest.raises(RuntimeError):
        slash.add_cleanup(lambda: None)


def test_cleanups(suite, suite_test):

    cleanup = suite_test.add_cleanup()

    summary = suite.run()

    assert summary.events[cleanup]


def test_cleanup_args_kwargs_deprecated():
    with slash.Session() as s:
        slash.add_cleanup(lambda: None, "arg1", arg2=1)
    [w] = s.warnings
    assert 'deprecated' in str(w).lower()


def test_cleanup_ordering(suite, suite_test):
    cleanup1 = suite_test.add_cleanup()
    cleanup2 = suite_test.add_cleanup()
    events = suite.run().events

    assert events[cleanup1].timestamp > events[cleanup2].timestamp


@pytest.mark.parametrize('fail_test', [True, False])
def test_errors_in_cleanup(suite, suite_test, fail_test):
    cleanup1 = suite_test.add_cleanup()
    cleanup2 = suite_test.add_cleanup(extra_code=['None.a = 2'])

    if fail_test:
        suite_test.when_run.raise_exception()
    else:
        suite_test.expect_error()

    summary = suite.run()

    assert summary.events[cleanup1].timestamp > summary.events[cleanup2].timestamp

    [result] = summary.get_all_results_for_test(suite_test)

    assert len(result.get_errors()) == 2 if fail_test else 1
    cleanup_error = result.get_errors()[-1]
    assert 'AttributeError' in str(cleanup_error)
    assert 'NoneType' in str(cleanup_error)


def test_add_test_cleanup_from_session_scope_forbidden(checkpoint):

    with slash.Session():
        with pytest.raises(IncorrectScope):
            slash.add_cleanup(checkpoint, scope='test')

    assert not checkpoint.called


def test_adding_implicit_scoped_cleanups_from_test_end_forbidden(suite, suite_test, checkpoint):

    @gossip.register('slash.test_end')
    def test_end():

        with pytest.raises(CannotAddCleanup):
            slash.add_cleanup(checkpoint)

    suite.run()
    assert not checkpoint.called


def test_adding_session_scoped_cleanups_from_test_end_allowed(suite, suite_test, checkpoint):

    @gossip.register('slash.test_end')
    def test_end():
        slash.add_cleanup(checkpoint, scope='session')

    suite.run()
    assert checkpoint.called_count == len(suite)


def test_adding_cleanups_from_test_fixtures(suite, suite_test):
    fixture = suite.slashconf.add_fixture(scope='session')
    @fixture.append_body
    def __code__():
        @slash.add_cleanup
        def cleanup():
            slash.context.result.data['fixture_called'] = True

    suite_test.depend_on_fixture(fixture)
    res = suite.run()
    assert 'fixture_called' not in res[suite_test].data
    assert res.session.results.global_result.data['fixture_called']


def test_adding_cleanups_from_test_fixtures_with_specific_scope(suite, suite_test):
    fixture = suite.slashconf.add_fixture(scope='session')
    @fixture.append_body
    def __code__():
        def cleanup():
            slash.context.result.data['fixture_called'] = True
        slash.add_cleanup(cleanup, scope='test')

    suite_test.depend_on_fixture(fixture)
    res = suite.run()
    assert res[suite_test].data['fixture_called']
    assert 'fixture_called' not in res.session.results.global_result.data



def test_get_current_cleanup_phase(suite_builder):

    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name,reimported

        def test_something():

            assert not slash.is_in_cleanup()
            assert slash.get_current_cleanup_phase() is None

            def session_cleanup():
                assert slash.is_in_cleanup()
                assert slash.get_current_cleanup_phase() == 'session'
            slash.add_cleanup(session_cleanup, scope='session')

            def module_cleanup():
                assert slash.is_in_cleanup()
                assert slash.get_current_cleanup_phase() == 'module'
            slash.add_cleanup(module_cleanup, scope='module')

            def regular_cleanup():
                assert slash.is_in_cleanup()
                assert slash.get_current_cleanup_phase() == 'test'
            slash.add_cleanup(regular_cleanup)

    suite_builder.build().run().assert_success(1)


def test_add_functools_partial_cleanup(suite_builder):
    @suite_builder.first_file.add_code
    def __code__(): # pylint: disable=unused-variable
        import slash # pylint: disable=redefined-outer-name,reimported
        import functools

        def cleanup_with_argument(x):
            pass

        def test_partial_cleanup():
            slash.add_cleanup(functools.partial(cleanup_with_argument, 5))

    suite_builder.build().run().assert_success(1)
