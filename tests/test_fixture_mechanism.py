import inspect
import itertools
from uuid import uuid1

import pytest
import slash
from slash.exceptions import CyclicFixtureDependency, UnresolvedFixtureStore, UnknownFixtures, InvalidFixtureScope
from slash.core.fixtures.parameters import bound_parametrizations_context, get_parametrizations
from slash.core.fixtures.fixture_store import FixtureStore


def test_fixture_initialization_order_is_preserved(store):

    _fixture = lambda f: store.add_fixture(slash.fixture(f))
    generation = itertools.count(1)

    @_fixture
    def fixture1():
        return next(generation)

    @_fixture
    def fixture2():
        return next(generation)

    @_fixture
    def fixture3():
        return next(generation)

    store.resolve()
    d = store.get_fixture_dict(['fixture1', 'fixture2', 'fixture3'])
    for i in [1, 2, 3]:
        assert d['fixture{0}'.format(i)] == i


def test_fixture_id_remains_even_when_context_popped(store):

    @slash.fixture
    def fixture0():
        pass

    store.push_namespace()
    store.add_fixture(fixture0)
    store.resolve()

    fixture_obj = store.get_fixture_by_name('fixture0')
    assert fixture_obj.fixture_func is fixture0
    fixture_id = fixture_obj.info.id
    assert store.get_fixture_by_id(fixture_id) is fixture_obj

    store.pop_namespace()

    with pytest.raises(UnknownFixtures):
        store.get_fixture_by_name('fixture0')

    assert store.get_fixture_by_id(fixture_id) is fixture_obj


def test_variations_no_names(store):
    assert list(store.iter_parametrization_variations([])) == [{}]


def test_adding_fixture_twice_to_store(store):

    @slash.fixture
    def fixture0():
        pass

    store.add_fixture(fixture0)
    fixtureobj = store.get_fixture_by_name('fixture0')
    store.add_fixture(fixture0)
    assert store.get_fixture_by_name('fixture0') is fixtureobj


def test_fixture_store_namespace_repr(store):

    @store.add_fixture
    @slash.fixture
    def fixture0():
        pass

    ns = store.get_current_namespace()
    assert str(ns) == repr(ns)
    assert repr(ns) == 'Fixtures: fixture0'


def test_fixture_parameters(store):

    @store.add_fixture
    @slash.fixture
    def value(x, a):
        assert a == 'a', 'Fixture got unexpectedly overriden by parameter'
        return x

    @store.add_fixture
    @slash.fixture
    def a():
        return 'a'

    @store.add_fixture
    @slash.fixture
    @slash.parametrize('a', [1, 2, 3])
    def x(a, b):
        return (a, b)

    @store.add_fixture
    @slash.parametrize('b', [4, 5, 6])
    @slash.fixture
    def b(b):
        return b

    store.resolve()

    variations = list(_get_all_values(store, 'value'))
    assert set(variations) == set(itertools.product([1, 2, 3], [4, 5, 6]))


def test_variation_equality(store):

    @store.add_fixture
    @slash.fixture
    @slash.parametrize('a', [1, 2, 3])
    def fixture(a):
        pass

    store.resolve()

    prev_variation = None
    for variation in store.iter_parametrization_variations(fixture_ids=[store.get_fixture_by_name('fixture').info.id]):
        assert variation == variation
        assert not (variation != variation)
        assert variation != prev_variation
        assert not (variation == prev_variation)
        prev_variation = variation


def _get_all_values(store, fixture_name):
    returned = []
    for variation in store.iter_parametrization_variations(fixture_ids=[store.get_fixture_by_name(fixture_name).info.id]):
        store.push_scope('test')
        with bound_parametrizations_context(variation):
            returned.append(
                store.get_fixture_dict([fixture_name])[fixture_name])
        store.pop_scope('test', in_failure=False, in_interruption=False)
    return returned


@pytest.mark.parametrize('scopes', [('module', 'test'), ('session', 'module'), ('session', 'test')])
def test_wrong_scoping(store, scopes):

    @store.add_fixture
    @slash.fixture(scope=scopes[0])
    def fixture1(fixture2):
        pass

    @store.add_fixture
    @slash.fixture(scope=scopes[1])
    def fixture2():
        pass

    with pytest.raises(InvalidFixtureScope):
        store.resolve()


def test_this_argument(store):

    @store.add_fixture
    @slash.fixture
    def sample(this, other):
        assert this.name == 'sample'
        assert other == 'ok_other'
        return 'ok_sample'

    @store.add_fixture
    @slash.fixture
    def other(this):
        assert this.name == 'other'
        return 'ok_other'

    store.resolve()

    assert store.get_fixture_dict(['sample']) == {
        'sample': 'ok_sample',
    }


def test_fixture_store_unresolved(store):

    @store.add_fixture
    @slash.fixture
    def some_fixture(a, b, c):
        return a + b + c

    with pytest.raises(UnresolvedFixtureStore):
        store.get_fixture_dict(['some_fixture'])


def test_fixture_store_resolve_missing_fixtures(store):

    @store.add_fixture
    @slash.fixture
    def some_fixture(a, b, c):
        return a + b + c

    with pytest.raises(UnknownFixtures):
        store.resolve()


def test_get_all_needed_parametrization_ids(store):

    @store.add_fixture
    @slash.fixture
    @slash.parametrize('param', [1, 2, 3])
    def fixture1(param):
        pass

    @store.add_fixture
    @slash.fixture
    def fixture2(fixture1):
        pass

    @store.add_fixture
    @slash.fixture
    @slash.parametrize('param', [4, 5, 6])
    def fixture3(fixture2, param):
        pass

    fixtureobj = store.get_fixture_by_id(fixture3.__slash_fixture__.id)

    with pytest.raises(UnresolvedFixtureStore):
        store.get_all_needed_parametrization_ids(fixtureobj)

    store.resolve()

    assert len(set(store.get_all_needed_parametrization_ids(fixtureobj))) == 2


def test_get_all_needed_parametrization_ids_of_parametrization(store):

    @store.add_fixture
    @slash.fixture
    @slash.parametrize('param', [1, 2, 3])
    def fixture1(param):
        pass

    fixtureobj = store.get_fixture_by_id(fixture1.__slash_fixture__.id)
    [param_fixtureobj] = get_parametrizations(fixture1)

    with pytest.raises(UnresolvedFixtureStore):
        store.get_all_needed_parametrization_ids(fixtureobj)

    store.resolve()

    needed = set(store.get_all_needed_parametrization_ids(param_fixtureobj))
    assert len(needed) == 1
    assert needed == set([param_fixtureobj.info.id])



def test_fixture_store_iter_parametrization_variations_missing_fixtures(store):

    def test_func(needed_fixture):
        pass

    with pytest.raises(UnknownFixtures):
        list(store.iter_parametrization_variations(funcs=[test_func]))


def test_fixture_store_iter_parametrization_variations_unresolved(store):

    @store.add_fixture
    @slash.fixture
    @slash.parametrize('x', [1, 2, 3])
    def needed_fixture(x):
        pass

    def test_func(needed_fixture):
        pass

    with pytest.raises(UnresolvedFixtureStore):
        list(store.iter_parametrization_variations(funcs=[test_func]))



def test_fixture_dependency(store):
    counter = itertools.count()

    @store.add_fixture
    @slash.fixture
    def fixture1(fixture2):
        assert fixture2 == 'fixture2_value_0'
        return 'fixture1_value_{0}'.format(next(counter))

    @store.add_fixture
    @slash.fixture
    def fixture2():
        return 'fixture2_value_{0}'.format(next(counter))

    store.resolve()

    assert store.get_fixture_dict(['fixture1', 'fixture2']) == {
        'fixture1': 'fixture1_value_1',
        'fixture2': 'fixture2_value_0',
    }


def test_nested_store_resolution_activation(store):

    store.push_namespace()

    @store.add_fixture
    @slash.fixture
    def fixture0():
        return '0'

    store.push_namespace()

    @store.add_fixture
    @slash.fixture
    def fixture1(fixture0):
        assert fixture0 == '0'
        return '1'

    store.push_namespace()

    @store.add_fixture
    @slash.fixture
    def fixture2(fixture1, fixture0):
        assert fixture0 == '0'
        assert fixture1 == '1'
        return '2'

    store.resolve()

    assert store.get_fixture_dict(['fixture2']) == {
        'fixture2': '2'
    }

    store.pop_namespace()

    with pytest.raises(UnknownFixtures):
        store.get_fixture_dict(['fixture2'])


def test_fixture_dependency_cycle():
    store = FixtureStore()

    @store.add_fixture
    @slash.fixture
    def fixture1(fixture2):
        return 1

    @store.add_fixture
    @slash.fixture
    def fixture2(fixture3):
        return 2

    @store.add_fixture
    @slash.fixture
    def fixture3(fixture1):
        return 3

    store.resolve()

    with pytest.raises(CyclicFixtureDependency):
        store.get_fixture_dict(['fixture1'])


def test_fixture_decorator():

    def func(a, b, c):
        pass

    assert not hasattr(func, '__slash_fixture__')

    assert slash.fixture(func) is func

    assert func.__slash_fixture__ is not None


def test_fixture_decorator_multiple_calls(fixture_func):
    fixture_info = fixture_func.__slash_fixture__
    assert slash.fixture(slash.fixture(fixture_func)) is fixture_func

    assert fixture_func.__slash_fixture__ is fixture_info


def test_fixture_required_fixtures(fixture_func):
    assert fixture_func.__slash_fixture__.required_args == inspect.getargspec(
        fixture_func).args


def test_fixture_name(fixture_func, fixture_func_name):
    assert fixture_func.__slash_fixture__.name == fixture_func_name


def test_fixture_store_add(fixture_func, fixture_func_name):
    f = FixtureStore()
    assert f.add_fixture(fixture_func) is fixture_func
    assert f.get_fixture_by_name(
        fixture_func_name).fixture_func is fixture_func

def test_nofixtures_decorator(store):

    @slash.nofixtures
    def func1(a, b, c):
        pass

    [var] = store.iter_parametrization_variations(funcs=[func1])
    assert var == {}

def test_nofixtures_decorator_methods(store):

    class TestClass(slash.Test):
        @slash.nofixtures
        def before(self, a, b, c):
            pass

    [var] = store.iter_parametrization_variations(methods=[('before', TestClass.before)])
    assert var == {}



@pytest.fixture(params=[True, False])
def fixture_func(request, fixture_func_name):

    def func(a, b, c, d):
        pass

    use_function_name = request.param
    if use_function_name:
        func.__name__ = fixture_func_name
        return slash.fixture(func)
    return slash.fixture(name=fixture_func_name)(func)


@pytest.fixture
def fixture_func_name():
    return str(uuid1()).replace('-', '_')


@pytest.fixture
def store():
    return FixtureStore()

@pytest.fixture(autouse=True)
def non_null_ctx(request):
    slash.ctx.push_context()
    request.addfinalizer(slash.ctx.pop_context)



@pytest.fixture
def cleanup_map():
    return {}


@pytest.fixture
def test_scoped_fixture(store, cleanup_map):

    return _get_scoped_fixture('test', store, cleanup_map)


@pytest.fixture
def module_scoped_fixture(store, cleanup_map):

    return _get_scoped_fixture('module', store, cleanup_map)


@pytest.fixture
def session_scoped_fixture(store, cleanup_map):

    return _get_scoped_fixture('session', store, cleanup_map)


def _get_scoped_fixture(scope, store, cleanup_map):
    @store.add_fixture
    @slash.fixture(scope=scope, name='{0}_scoped_fixture'.format(scope))
    def fixture(this):

        @this.add_cleanup
        def cleanup():
            cleanup_map[this.name] = True

        return ok(this.name)
    return fixture


def ok(s):
    return 'ok_{0}'.format(s)
