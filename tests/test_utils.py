import pytest
import slash
import time
import logbook
from slash.utils.interactive import notify_if_slow_context
from slash.reporting.console_reporter import ConsoleReporter
from slash._compat import StringIO


@pytest.mark.parametrize('show_duration', [True, False])
def test_notify_if_slow_context(show_duration):
    output_stream = StringIO()
    reporter = ConsoleReporter(logbook.TRACE, output_stream)
    with slash.Session(console_stream=output_stream, reporter=reporter):
        with notify_if_slow_context('message', slow_seconds=0.1, end_message='End', show_duration=show_duration):
            time.sleep(1)
    output = output_stream.getvalue()
    assert 'message' in output
    assert 'End' in output
    assert ('took 0:00:01' in output) == show_duration
