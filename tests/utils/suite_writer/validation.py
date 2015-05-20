import itertools

import logbook

from slash._compat import iteritems, itervalues, xrange

_logger = logbook.Logger(__name__)


def validate_run(suite, run_result, expect_interruption):
    if expect_interruption or not run_result.session.results.is_success(allow_skips=True):
        assert run_result.exit_code != 0, 'slash run unexpectedly returned 0'
    else:
        assert run_result.exit_code == 0

    for test, results in iteritems(_group_results_by_test_id(suite, run_result)):
        _validate_single_test(test, results)


def _validate_single_test(test, results):

    for param_values in _iter_param_value_sets(test):

        for repetition in xrange(test.get_num_expected_repetitions()):

            for index, result in enumerate(results):

                if _result_matches(test, result, param_values):

                    results.pop(index)

                    _validate_single_test_result(test, result)

                    break
            else:
                assert False, 'Could not find parameter set {0}'.format(
                    param_values)

    assert not results, 'Unmatched results exist'


def _iter_param_value_sets(test):
    params = _find_all_parameters(test)
    param_ids = [p.id for p in params]
    for combination in itertools.product(*(param.values for param in params)):
        yield dict(zip(param_ids, combination))


def _find_all_parameters(func):
    returned = {}
    stack = [func]
    while stack:
        f = stack.pop()
        stack.extend(f.get_fixtures())
        for param in f.get_parameters():
            if param.id not in returned:
                returned[param.id] = param
    return list(itervalues(returned))


def _result_matches(test, result, param_values):
    return result.data.get('param_values', {}) == param_values


def _validate_single_test_result(test, result):
    expected = test.get_expected_result()
    if expected == 'ERROR':
        assert result.is_error(), 'Test did not issue error as expected'
    elif expected == 'FAIL':
        assert result.is_failure(), 'Test did not fail as expected'
    elif expected == 'SUCCESS':
        assert result.is_success(), 'Test {0} unexpectedly unsuccessful:\n{1}'.format(
            test.id, list(itertools.chain(result.get_errors(), result.get_failures())))
    elif expected == 'INTERRUPT':
        assert result.is_interrupted(), 'Test did not get interrupted as expected'
    elif expected == 'SKIP':
        assert result.is_skip()
    elif expected == 'NOT_RUN':
        assert result.is_not_run()
    else:
        raise NotImplementedError(
            'Unknown expected result: {0!r}'.format(expected))  # pragma: no cover


def _group_results_by_test_id(suite, run_result):
    tests_by_id = dict((t.id, t) for t in suite)
    unseen = tests_by_id.copy()

    groups = {}

    for result in run_result.session.results:
        if 'Interactive' ==  result.test_metadata.address:
            continue
        test_id = get_test_id_from_test_address(result.test_metadata.address)
        assert tests_by_id[test_id].is_selected()
        groups.setdefault(tests_by_id[test_id], []).append(result)
        unseen.pop(test_id, None)

    for test_id, test in list(iteritems(unseen)):
        if not test.is_selected():
            unseen.pop(test_id, None)

    assert not unseen, 'Expected results not found ({0})'.format(unseen)

    return groups


def get_test_id_from_test_address(addr):
    return addr.rsplit('.', 1)[-1].split('_', 1)[1].split('(')[0]
