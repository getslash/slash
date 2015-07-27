import logbook

import pytest
from slash._compat import StringIO
from slash.reporting.console_reporter import ConsoleReporter


def test_console_reporter(suite, level, config_override):
    config_override('log.console_level', level)
    summary = suite.run()
    suite.add_test().when_run.raise_exception()
    assert summary.get_console_output()


def test_silence_manual_errors(suite, suite_test, config_override):
    suite_test.append_line('slash.add_error("msg")')
    suite_test.expect_error()
    config_override('log.show_manual_errors_tb', False)
    output = suite.run().get_console_output()
    assert 'slash.add_error' not in output


@pytest.fixture(params=list(range(logbook.DEBUG, logbook.CRITICAL + 1)))
def level(request):
    return request.param

@pytest.fixture
def stream():
    return StringIO()
