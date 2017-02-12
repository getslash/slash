# pylint: disable=redefined-outer-name
import pytest
from slash._compat import StringIO
from slash.reporting.console_reporter import TerminalWriterWrapper


def test_line_in_progress_no_newline(tw):
    tw.write('.')
    tw.write('.')
    assert tw._line == '..'  # pylint: disable=protected-access


def test_line_in_progress_with_newline(tw):
    tw.write('this is \n a half line')
    assert tw._line == ' a half line'  # pylint: disable=protected-access


def test_line_in_progress_with_end(tw):
    tw.write('line here\n')
    assert tw._line == ''  # pylint: disable=protected-access


@pytest.fixture
def tw():
    return TerminalWriterWrapper(StringIO())
