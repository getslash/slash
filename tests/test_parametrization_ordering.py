import pytest
import slash

import itertools
from .utils import run_tests_in_session


@pytest.mark.parametrize('on_fixture', [True, False])
def test_stable_ordering(on_fixture):
    """Make sure that cartesian products in parametrizations are stable, even when changing the order of the parametrization decorators
    """
    params = [('a', [1, 2, 3]), ('b', [True, False]), ('c', [4, 5, 6])]
    permutations = list(itertools.permutations(params))

    def generate_session_and_test(permutation):

        s = slash.Session()

        if on_fixture:

            @slash.fixture
            def some_fixture(a, b, c):
                return {'a': a, 'b': b, 'c': c}

            parametrized = some_fixture

            def test_something(some_fixture):
                slash.context.result.data['params'] = some_fixture
        else:
            def test_something(a, b, c):
                slash.context.result.data['params'] = {'a': a, 'b': b, 'c': c}
            parametrized = test_something

        for param_name, values in permutation:
            parametrized = slash.parametrize(param_name, values)(parametrized)

        if on_fixture:
            s.fixture_store.push_namespace()
            s.fixture_store.add_fixture(some_fixture)
            s.fixture_store.pop_namespace()
        s.fixture_store.resolve()

        return s, test_something

    results_by_permutation = []
    for p in permutations:
        session, test = generate_session_and_test(p)
        res = run_tests_in_session(test, session=session)
        assert res.is_success(), 'run failed'
        results_by_permutation.append(res)

    param_values = {}
    for results in results_by_permutation:
        for index, result in enumerate(results):
            for param_name, param_value in result.data['params'].items():
                param_values.setdefault((param_name, index), []).append(param_value)

    for (param_name, index), values in param_values.items():
        assert len(set(values)) == 1, '{}#{} is not stable: {}'.format(param_name, index, values)
