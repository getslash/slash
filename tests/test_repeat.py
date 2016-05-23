import pytest


@pytest.mark.parametrize('parametrize', [True, False])
def test_repeating_test(suite, suite_test, parametrize):
    num_repetitions = 5
    suite_test.repeat(num_repetitions)

    if parametrize:
        param = suite_test.add_parameter()

    summary = suite.run()
    results = summary.get_all_results_for_test(suite_test)
    if parametrize:
        assert len(results) == num_repetitions * len(param.values)
    else:
        assert len(results) == num_repetitions
    assert len(set(result.test_metadata.id for result in results)) == len(results)


def test_global_repeat(suite, config_override):
    num_repetitions = 5
    config_override('run.repeat_each', num_repetitions)
    for test in suite:
        test.expect_repetition(num_repetitions)
    assert suite.run().ok()
