import colorama
import pytest
from slash._compat import StringIO
from slash.utils.cli_utils import Printer, make_styler, UNDERLINED

_style_1 = colorama.Fore.MAGENTA + colorama.Style.BRIGHT + UNDERLINED  # pylint: disable=no-member
_style_2 = colorama.Fore.GREEN + colorama.Style.BRIGHT  # pylint: disable=no-member

def _toggle(toggle_name):
    return pytest.mark.parametrize(toggle_name, [True, False])

def _colorized(string, style=None):
    if not style:
        return string
    return make_styler(style)(string)

@_toggle('force_color')
@_toggle('enable_color')
def test_printer_with_output_disabled(force_color, enable_color):
    report_stream = StringIO()
    printer = Printer(report_stream, enable_output=False, force_color=force_color, enable_color=enable_color)
    printer(_colorized('A', _style_1))
    printer(_colorized('B', _style_2))
    printer('C')
    assert not report_stream.getvalue()


def test_printer_with_forced_colored():
    report_stream = StringIO()
    printer = Printer(report_stream, force_color=True)
    expected_lines = []
    for string, style in [('A', _style_1), ('B', _style_2), ('C', None)]:
        colored_string = _colorized(string, style)
        printer(colored_string)
        expected_lines.append(colored_string.colorize() if style else str(colored_string))
    assert report_stream.getvalue().splitlines() == expected_lines


def test_printer_with_disalbed_colored():
    report_stream = StringIO()
    printer = Printer(report_stream, enable_color=True)
    printer(_colorized('A', _style_1))
    printer(_colorized('B', _style_2))
    printer('C')
    assert report_stream.getvalue().splitlines() == ['A', 'B', 'C']
