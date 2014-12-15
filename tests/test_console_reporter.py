import logbook

import pytest
from slash._compat import StringIO
from slash.reporting.console_reporter import ConsoleReporter


def test_console_reporter(level, stream, populated_suite):

    reporter = ConsoleReporter(level=level, stream=stream)
    a, b, c, d = list(populated_suite)[:4]
    a.error()
    b.fail()
    c.skip()
    populated_suite.run(reporter=reporter)


@pytest.fixture(params=list(range(logbook.DEBUG, logbook.CRITICAL + 1)))
def level(request):
    return request.param

@pytest.fixture
def stream():
    return StringIO()
