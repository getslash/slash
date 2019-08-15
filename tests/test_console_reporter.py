import logbook
import pytest

from io import StringIO
from slash.reporting.console_reporter import ConsoleReporter


@pytest.mark.parametrize('console_level', [True, False])  # pylint: disable=redefined-outer-name
def test_console_reporter(suite, level, config_override, console_level):  # pylint: disable=redefined-outer-name
    config_override('log.color_console', console_level)
    config_override('log.console_level', level)
    summary = suite.run()
    suite.add_test().when_run.raise_exception()
    output = summary.get_console_output()
    assert output
    assert bool(console_level) == ('\x1b' in output)


def test_silence_manual_errors(suite, suite_test, config_override):
    suite_test.append_line('slash.add_error("msg")')
    suite_test.expect_error()
    config_override('log.show_manual_errors_tb', False)
    output = suite.run().get_console_output()
    assert 'slash.add_error' not in output


def test_num_collected_printed_once(suite, suite_test):  # pylint: disable=unused-argument
    assert len(suite) > 1
    output = suite.run().get_console_output()
    assert output.count('collected') == 1


@pytest.mark.parametrize('long_headline', [True, False])
@pytest.mark.parametrize('multiline', [True, False])
def test_fancy_message(long_headline, multiline):
    output = StringIO()
    reporter = ConsoleReporter(logbook.TRACE, output)
    headline = 'some headline here'
    if long_headline:
        headline *= 80
    message = 'some message here'

    repetitions = 5
    if multiline:
        message = "\n".join(message for i in range(repetitions))
        message += '\n\n'

    reporter.report_fancy_message(headline, message)
    if long_headline:
        assert headline[:80] in output.getvalue()
    else:
        assert headline in output.getvalue()

    if multiline:
        assert output.getvalue().count(message.splitlines()[0]) == repetitions
    else:
        assert output.getvalue().count(message) == 1


def test_console_reporter_with_closed_stream(forge):
    def raise_io_error(*args, **kwargs):
        raise IOError('args: {!r}, kwargs: {!r}'.format(args, kwargs))
    output = StringIO()
    reporter = ConsoleReporter(logbook.TRACE, output)
    forge.replace_with(reporter._terminal._writer, 'write', raise_io_error)  # pylint: disable=protected-access
    reporter.report_message('Hello')
    reporter.report_error_message('Error')

    forge.replay()
    forge.restore_all_replacements()


@pytest.fixture(params=list(range(logbook.DEBUG, logbook.CRITICAL + 1)))
def level(request):
    return request.param


@pytest.fixture
def stream():
    return StringIO()
