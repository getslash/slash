def test_repeating_test(suite, suite_test):
    num_repetitions = 5
    suite_test.repeat(num_repetitions)

    summary = suite.run()
    results = summary.get_all_results_for_test(suite_test)
    assert len(results) == num_repetitions
    assert len(set(result.test_metadata.id for result in results)) == len(results)

