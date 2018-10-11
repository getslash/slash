# pylint: disable=unused-variable, unused-argument
import functools

import pytest
import itertools
import slash
from slash.exceptions import UnknownFixtures

from .utils import make_runnable_tests


def test_resolve_fixture_object():
    with slash.Session() as s:

        @s.fixture_store.add_fixture
        @slash.parametrize('x', [1, 2])
        @slash.fixture
        def fixture1(x):
            pass

        @s.fixture_store.add_fixture
        @slash.parametrize('x', [3, 4])
        @slash.fixture
        def fixture2(fixture1, x):
            pass

        def test_something(fixture2):
            pass

        s.fixture_store.resolve()

        with s.get_started_context():
            tests = make_runnable_tests(test_something)

    _resolve = functools.partial(s.fixture_store.resolve_name, start_point=tests[0])
    def _resolve_values(path):
        return [v.value for v in _resolve(path).values]

    # check simple resolutions
    assert _resolve('fixture2').info is fixture2.__slash_fixture__
    assert _resolve('fixture2.fixture1').info is fixture1.__slash_fixture__

    # check parameter resolution
    assert _resolve_values('fixture2.fixture1.x') == [1, 2]
    assert _resolve_values('fixture2.x') == [3, 4]

    for invalid_name in ['fixture2.x.y']:
        with pytest.raises(UnknownFixtures):
            _resolve(invalid_name)

def test_resolve_fixture_object_namespace_correctness():
    with slash.Session() as s:

        store = s.fixture_store

        @store.add_fixture
        @slash.fixture
        def global_fixture_1(dependency_fixture):
            pass

        @store.add_fixture
        @slash.fixture
        def dependency_fixture():
            pass

        expected = dependency_fixture

        store.push_namespace()

        @store.add_fixture
        @slash.fixture
        def local_fixture(global_fixture_1):
            pass

        @store.add_fixture
        @slash.fixture
        def dependency_fixture():         # pylint: disable=function-redefined
            pass

        def test_something(local_fixture):
            pass

        store.resolve()

        with s.get_started_context():
            tests = make_runnable_tests(test_something)

        test = tests[0]
        resolved = store.resolve_name('local_fixture.global_fixture_1.dependency_fixture', test, namespace=test.get_fixture_namespace()).info
        assert resolved is expected.__slash_fixture__


def test_invalid_name():
    with slash.Session() as s:
        with pytest.raises(UnknownFixtures):
            s.fixture_store.resolve_name('', start_point=object())


def test_resolve_fixture_parameterization_with_scopes(suite_builder):
    # pylint: disable=unused-variable
    @suite_builder.first_file.add_code
    def __code__():
        import slash # pylint: disable=redefined-outer-name, reimported
        @slash.parametrize('x', [1, 2])
        @slash.fixture(scope='session')
        def session_fixture(x):
            return x

        @slash.parametrize('x', [3, 4])
        @slash.fixture(scope='module')
        def module_fixture(x):
            return x

        @slash.parametrize('x', [5, 6])
        @slash.fixture
        def fixture_test(x):
            return x

        def test_1(session_fixture, module_fixture, fixture_test):
            slash.context.result.data['params'] = (session_fixture, module_fixture, fixture_test)

    suite_builder.build().run().assert_success(8).with_data([{'params': x} for x in list(itertools.product(range(1, 3), range(3, 5), range(5, 7)))])


def test_interdependent_fixtures_called_once(suite_builder):
    # See https://github.com/getslash/slash/issues/882
    # pylint: disable=unused-variable, redefined-outer-name,reimported
    @suite_builder.first_file.add_code
    def __code__():
        import slash
        import uuid


        @slash.fixture
        def fixture_2(fixture_1):
            return 'improved-{}'.format(fixture_1)

        @slash.fixture
        @slash.parameters.toggle("toggle")
        def fixture_1(toggle):
            return str(uuid.uuid4())


        def test_1(fixture_1, fixture_2):
            assert fixture_1 in fixture_2

    suite_builder.build().run().assert_success(2)
