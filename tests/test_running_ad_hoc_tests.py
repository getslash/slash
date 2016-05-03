"""Slash should support running ad-hoc test objects, that were not loaded from a file
"""
import pytest
import slash


@pytest.mark.parametrize('is_class', [True, False])
def test_ad_hoc_test_running(checkpoint, is_class):

    if is_class:
        class test_sample(slash.Test):

            def test_something(self):
                checkpoint()

    else:
        def test_sample():
            checkpoint()

    with slash.Session() as session:
        with session.get_started_context():
            slash.runner.run_tests(slash.loader.Loader().get_runnables(test_sample))
    assert session.results.is_success()
    assert checkpoint.called
