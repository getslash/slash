# pylint: disable=redefined-outer-name
from uuid import uuid4
import logbook
import pytest


def test_unified_session_log_has_test_log(unified_log, log_marker):
    with open(unified_log) as f:
        assert log_marker in f.read()

def test_unified_session_log_failure_log_still_in_test_log(unified_run, test_result, log_marker):  # pylint: disable=unused-argument
    with open(test_result.get_log_path()) as f:
        assert log_marker in f.read()

def test_warnings_propagation(unified_run):
    assert len(unified_run.session.warnings) > 0  # pylint: disable=len-as-condition


@pytest.fixture  # pylint: disable=unused-argument
def unified_log(unified_run, tmpdir):  # pylint: disable=unused-argument
    return str(tmpdir.join('session.log'))

@pytest.fixture
def test_result(unified_run, suite_test):
    [returned] = unified_run.get_all_results_for_test(suite_test)
    return returned


@pytest.fixture
def unified_run(suite, suite_test, tmpdir, config_override, log_marker):
    config_override('log.core_log_level', logbook.TRACE)
    config_override('log.unified_session_log', True)
    config_override('log.root', str(tmpdir))
    config_override('log.session_subpath', 'session.log')
    suite_test.append_line('slash.logger.info({0!r})'.format(log_marker))
    suite_test.append_line('slash.logger.warning({0!r})'.format('warning'))
    return suite.run()


@pytest.fixture
def log_marker():
    return 'log_marker_{0}'.format(uuid4())
