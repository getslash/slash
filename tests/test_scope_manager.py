# pylint: disable=redefined-outer-name
import collections
import functools
import itertools

import pytest
import slash
from slash.core.scope_manager import ScopeManager, get_current_scope
from .utils import make_runnable_tests
from .utils.suite_writer import Suite


def test_requirement_mismatch_end_of_module():
    """Test that unmet requirements at end of file(module) still enable scope manager to detect the end and properly pop contextx"""

    suite = Suite()

    num_files = 3
    num_tests_per_file = 5

    for i in range(num_files):  # pylint: disable=unused-variable
        file1 = suite.add_file()

        for j in range(num_tests_per_file):  # pylint: disable=unused-variable
            file1.add_function_test()

        t = file1.add_function_test()
        t.add_decorator('slash.requires(lambda: False)')
        t.expect_skip()

    suite.run()


def test_scope_manager(dummy_fixture_store, scope_manager, tests_by_module):
    # pylint: disable=protected-access
    last_scopes = None
    for module_index, tests in enumerate(tests_by_module):
        for test_index, test in enumerate(tests):
            scope_manager.begin_test(test)
            assert dummy_fixture_store._scopes == ['session', 'module', 'test']
            expected = _increment_scope(
                last_scopes,
                test=1,
                module=1 if test_index == 0 else 0,
                session=1 if test_index == 0 and module_index == 0 else 0)
            assert dummy_fixture_store._scope_ids == expected
            # make sure the dict is copied
            assert expected is not dummy_fixture_store._scope_ids
            last_scopes = expected
            scope_manager.end_test(test)
            assert dummy_fixture_store._scopes == ['session', 'module']
            assert dummy_fixture_store._scope_ids == last_scopes

    scope_manager.flush_remaining_scopes()
    assert not dummy_fixture_store._scopes


def test_get_current_scope(suite_builder):

    @suite_builder.first_file.add_code
    def __code__():
        # pylint: disable=unused-variable,redefined-outer-name,reimported
        import slash
        import gossip

        TOKEN = 'testing-current-scope-token'

        def _validate_current_scope(expected_scope):
            assert slash.get_current_scope() == expected_scope

        @gossip.register('slash.after_session_start', token=TOKEN)
        def session_validation():
            assert slash.get_current_scope() == 'session'

        @gossip.register('slash.configure', token=TOKEN)
        @gossip.register('slash.app_quit', token=TOKEN)
        def _no_scope():
            assert slash.get_current_scope() is None

        def test_something():
            assert slash.get_current_scope() == 'test'

        gossip.unregister_token(TOKEN)

    suite_builder.build().run().assert_success(1)
    assert get_current_scope() is None


@pytest.fixture
def scope_manager(dummy_fixture_store, forge):
    session = slash.Session()
    forge.replace_with(session, 'fixture_store', dummy_fixture_store)
    return ScopeManager(session)


@pytest.fixture
def dummy_fixture_store():
    return DummyFixtureStore()


@pytest.fixture
def tests_by_module():

    def test_func():
        pass

    num_modules = 5
    num_tests_per_module = 3
    returned = []

    with slash.Session():
        for module_index in range(num_modules):
            module_name = '__module_{}'.format(module_index)
            returned.append([])
            for test_index in range(num_tests_per_module):  # pylint: disable=unused-variable
                [test] = make_runnable_tests(test_func)  # pylint: disable=unbalanced-tuple-unpacking
                assert test.__slash__.module_name
                test.__slash__.module_name = module_name
                returned[-1].append(test)
    return returned


def _increment_scope(prev_scopes, **increments):
    if not prev_scopes:
        returned = {}
    else:
        returned = prev_scopes.copy()
    for key, value in increments.items():
        if value == 0:
            continue
        if key not in returned:
            returned[key] = 0
        returned[key] += value
    return returned


class DummyFixtureStore(object):

    def __init__(self):
        super(DummyFixtureStore, self).__init__()
        self._scopes = []
        self._counters = collections.defaultdict(
            functools.partial(itertools.count, 1))
        self._scope_ids = {}

    def push_scope(self, scope):
        self._scopes.append(scope)
        self._scope_ids[scope] = next(self._counters[scope])

    def pop_scope(self, scope):
        latest_scope = self._scopes.pop()
        assert latest_scope == scope
