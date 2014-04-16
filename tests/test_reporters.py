import inspect

import pytest
from slash.reporting.console_reporter import ConsoleReporter
from slash.reporting.null_reporter import NullReporter
from slash.reporting.reporter_interface import ReporterInterface


@pytest.fixture(params=[NullReporter, ConsoleReporter])
def reporter_class(request):
    return request.param

def test_reporters_inherit_from_interface(reporter_class):
    assert issubclass(reporter_class, ReporterInterface)

def test_reporters_conform_to_interface(reporter_class):
    def _dir(cls):
        return set(name for name in dir(cls) if not name.startswith("_"))

    assert _dir(reporter_class) <= _dir(ReporterInterface)

def test_parameter_lists_conform_to_interface(reporter_class):
    for method_name in dir(reporter_class):
        if method_name.startswith("_"):
            continue

        argpsec = inspect.getargspec(getattr(reporter_class, method_name))
        expected = inspect.getargspec(getattr(ReporterInterface, method_name))
        assert argpsec == expected
