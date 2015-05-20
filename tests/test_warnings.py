import pytest
import slash

from .utils import run_tests_assert_success, without_pyc


@pytest.mark.parametrize('reprify', [repr, str])
def test_str_repr(warning, reprify):
    assert 'this is a warning' in reprify(warning)

def test_location(warning):
    assert warning.details['filename'] == without_pyc(__file__)

def test_to_dict(warning):
    assert isinstance(warning.to_dict(), dict)

@pytest.fixture
def warning():
    class SampleTest(slash.Test):
        def test(self):
            slash.logger.warning("this is a warning. Param: {0}", 1)

    session = run_tests_assert_success(SampleTest)

    assert len(session.warnings) == 1

    [warning] = session.warnings
    return warning
