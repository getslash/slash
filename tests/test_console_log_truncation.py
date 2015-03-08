import logbook

import pytest
import slash
from slash._compat import StringIO
from slash.log import ConsoleHandler


@pytest.mark.parametrize('use_truncation', [True, False])
def test_line_truncation(long_text, use_truncation, config_override):

    config_override('log.truncate_console_lines', use_truncation)
    config_override('log.console_level', logbook.DEBUG)

    console = StringIO()

    with slash.Session(console_stream=console):
        logbook.debug(long_text)

    if use_truncation:
        assert long_text not in console.getvalue()
        assert long_text[:20] in console.getvalue()
    else:
        assert long_text in console.getvalue()


@pytest.fixture
def long_text():
    return 'a' * 200
