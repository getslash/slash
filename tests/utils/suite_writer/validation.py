import itertools
import re

import logbook

from slash._compat import iteritems, itervalues, xrange

from .generator_fixture import GeneratorFixture

_logger = logbook.Logger(__name__)


def validate_run(suite, run_result, expect_interruption, expect_session_errors):
    if expect_interruption:
        assert run_result.session.results.global_result.is_interrupted(), \
        'Session global result is not marked as interrupted, even though interruption was expected'

    if expect_interruption or not run_result.session.results.is_success(allow_skips=True):
        assert run_result.exit_code != 0, '`slash run` unexpectedly returned 0'
    else:
        assert run_result.exit_code == 0, '`slash run` unexpectedly returned {}. Output: {}'.format(
            run_result.exit_code, run_result.get_console_output())

    global_result = run_result.session.results.global_result
    errors = global_result.get_errors() + global_result.get_failures()
    if expect_session_errors:
        assert errors, 'Expected session errors but found none'
    else:
        assert not errors, 'Sessions errors were not expected (Got {})'.format(errors)

    for test, results in iteritems(_group_results_by_test_id(suite, run_result)):
        _validate_single_test(test, results)


def _validate_single_test(test, results):

    param_names = {p.id: p.name for p in _find_all_parameters(test)}

    for param_values in _iter_param_value_sets(test):

        is_excluded = any((param_names[param_id], value) in test.excluded_param_values for param_id, value in param_values.items())

        for repetition in xrange(test.get_num_expected_repetitions()):  # pylint: disable=unused-variable

            for index, result in enumerate(results):

                if _result_matches(result, param_values):

                    results.pop(index)

                    if is_excluded:
                        assert result.is_skip()
                    else:
                        _validate_single_test_result(test, result)

                    break
            else:
                assert False, 'Could not find parameter set {}'.format(
                    param_values)

    assert not results, 'Unmatched results exist'


def _iter_param_value_sets(test):
    params = _find_all_parameters(test)
    param_ids = [p.id for p in params]
    for combination in itertools.product(*(param.values for param in params)):
        yield dict(zip(param_ids, combination))


def _find_all_parameters(func):
    params = []
    stack = [func]
    while stack:
        f = stack.pop()
        for subfixture in f.get_fixtures():
            if isinstance(subfixture, GeneratorFixture):
                params.append(subfixture)
                continue
            else:
                stack.append(subfixture)
        params.extend(f.get_parameters())
    return list(itervalues({p.id: p for p in params}))


def _result_matches(result, param_values):
    values = result.test_metadata.variation.values.copy()
    for param_name in list(values):
        # handle the case of a fixture with a single param, which is logically a parameter by itself
        if re.match(r'^fx_\d+.param$', param_name):
            values_name = param_name.split('_')[1].split('.')[0]
        else:
            values_name = param_name.rsplit('_', 1)[-1]

        values[values_name] = values.pop(param_name)

    return values == param_values


def _validate_single_test_result(test, result):
    expected = test.get_expected_result()
    if expected == 'ERROR':
        assert result.is_error(), 'Test did not issue error as expected'
    elif expected == 'FAIL':
        assert result.is_failure(), 'Test did not fail as expected'
    elif expected == 'SUCCESS':
        assert result.is_success(), 'Test {} unexpectedly unsuccessful:\n{}'.format(
            test.id, list(itertools.chain(result.get_errors(), result.get_failures())))
    elif expected == 'INTERRUPT':
        assert result.is_interrupted(), 'Test did not get interrupted as expected'
    elif expected == 'SKIP':
        assert result.is_skip()
    elif expected == 'NOT_RUN':
        assert result.is_not_run()
    else:
        raise NotImplementedError(
            'Unknown expected result: {!r}'.format(expected))  # pragma: no cover


def _group_results_by_test_id(suite, run_result):
    tests_by_id = dict((t.id, t) for t in suite)
    unseen = tests_by_id.copy()

    groups = {}

    for result in run_result.session.results:
        if result.test_metadata.is_interactive():
            continue
        test_id = get_test_id_from_test_address(result.test_metadata.address)
        assert tests_by_id[test_id].is_selected(), 'Test {} appears in results, although not expected!'.format(test_id)
        groups.setdefault(tests_by_id[test_id], []).append(result)
        unseen.pop(test_id, None)

    for test_id, test in list(iteritems(unseen)):
        if not test.is_selected():
            unseen.pop(test_id, None)

    assert not unseen, 'Expected results not found ({})'.format(unseen)

    return groups


def get_test_id_from_test_address(addr):
    _, addr = addr.split(':', 1)
    return addr.split('_')[1].split('(')[0]
