def test_repeating_test(suite, suite_test):
    num_repetitions = 5
    suite_test.repeat(num_repetitions)

    summary = suite.run()
    results = summary.get_all_results_for_test(suite_test)
    assert len(results) == num_repetitions
    assert len(set(result.test_metadata.id for result in results)) == len(results)


def test_global_repeat(suite, config_override):
    num_repetitions = 5
    config_override('run.repeat_each', num_repetitions)
    for test in suite:
        test.expect_repetition(num_repetitions)
    assert suite.run().ok()
