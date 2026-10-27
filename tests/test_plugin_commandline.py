import pytest


@pytest.mark.parametrize("with_without", ["with", "without"])
def test_with_without_nonexisting_plugin(suite, with_without):
    summary = suite.run(additional_args=[f"--{with_without}-nonexisting-plugin"], verify=False)
    assert summary.exit_code != 0
