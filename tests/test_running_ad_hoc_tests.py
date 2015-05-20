"""Slash should support running ad-hoc test objects, that were not loaded from a file
"""
import slash
from slash.core.runnable_test import RunnableTest


def test_ad_hoc_test_running(checkpoint):

    class SampleTest(RunnableTest):
        def run(self):
            checkpoint()

        def get_requirements(self):
            return []

    with slash.Session() as session:
        with session.get_started_context():
            slash.runner.run_tests([SampleTest()])
    assert session.results.is_success()
