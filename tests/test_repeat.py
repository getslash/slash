import pytest


@pytest.mark.parametrize('parametrize', [True, False])
def test_repeating_each_test(suite, suite_test, parametrize):
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


def test_repeat_each_global(suite, config_override):
    num_repetitions = 5
    config_override('run.repeat_each', num_repetitions)
    for test in suite:
        test.expect_repetition(num_repetitions)
    assert suite.run().ok()

def test_repeat_all_global(suite, config_override):
    num_repetitions = 5
    config_override('run.repeat_all', num_repetitions)
    for index, test in enumerate(suite):
        test.append_line('slash.context.result.data["index"]={}'.format(index))

    for test in suite:
        test.expect_repetition(num_repetitions)

    summary = suite.run()

    indices = [res.data['index'] for res in summary.session.results.iter_test_results()]
    assert indices == [x for x in range(len(suite)) for _ in range(num_repetitions)]
