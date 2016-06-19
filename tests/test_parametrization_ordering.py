import slash

import itertools
from .utils import run_tests_assert_success


def test_stable_ordering():
    """Make sure that cartesian products in parametrizations are stable, even when changing the order of the parametrization decorators
    """
    params = [('a', [1, 2, 3]), ('b', [True, False]), ('c', [4, 5, 6])]
    permutations = list(itertools.permutations(params))

    def generate_test(permutation):

        def test_something(a, b, c):
            slash.context.result.data['params'] = {'a': a, 'b': b, 'c': c}

        for param_name, values in permutation:
            test_something = slash.parametrize(param_name, values)(test_something)

        return test_something

    results_by_permutation = [run_tests_assert_success(generate_test(p)).results
                              for p in permutations]

    param_values = {}
    for results in results_by_permutation:
        for index, result in enumerate(results):
            for param_name, param_value in result.data['params'].items():
                param_values.setdefault((param_name, index), []).append(param_value)

    for (param_name, index), values in param_values.items():
        assert len(set(values)) == 1, '{}#{} is not stable: {}'.format(param_name, index, values)
