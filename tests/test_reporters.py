import pytest

from slash.reporting.reporter_interface import ReporterInterface
from slash.reporting.null_reporter import NullReporter
from slash.reporting.console_reporter import ConsoleReporter

@pytest.mark.parametrize("reporter_class", [NullReporter, ConsoleReporter])
def test_reporters_conform_to_interface(reporter_class):
    def _dir(cls):
        return set(name for name in dir(cls) if not name.startswith("_"))

    assert _dir(reporter_class) <= _dir(ReporterInterface)
