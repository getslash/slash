#pylint: disable=unused-variable
import warnings
from uuid import uuid4

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


def test_warning_added_hook(suite, suite_test):

    captured = []

    @slash.hooks.register
    def warning_added(warning):
        captured.append(warning)

    suite_test.append_line('slash.logger.warning("message here")')
    suite.run()
    assert captured
    [w] = captured # pylint: disable=unbalanced-tuple-unpacking
    assert w.message == 'message here'
    assert isinstance(w.lineno, int)
    assert isinstance(w.filename, str)
    assert w.lineno
    assert w.filename


def test_native_warnings(message):

    def test_example():
        warnings.warn(message)

    s = run_tests_assert_success(test_example)

    assert len(s.warnings) == 1
    [w] = s.warnings
    assert w.message == message


@pytest.fixture
def message():
    return 'some message here {}'.format(uuid4())

@pytest.fixture
def warning():
    class SampleTest(slash.Test):

        def test(self):
            slash.logger.warning("this is a warning. Param: {0}", 1)

    session = run_tests_assert_success(SampleTest)

    assert len(session.warnings) == 1

    [warning] = session.warnings
    return warning
