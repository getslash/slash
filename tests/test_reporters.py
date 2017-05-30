import pytest
from slash.reporting.console_reporter import ConsoleReporter
from slash.reporting.null_reporter import NullReporter
from slash.reporting.reporter_interface import ReporterInterface
from slash.utils.python import get_underlying_func, get_arguments

# pylint: disable=redefined-outer-name


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

        derived_method = _get_method(reporter_class, method_name)
        base_method = _get_method(ReporterInterface, method_name)

        argpsec = [argument.name for argument in get_arguments(derived_method)]
        expected = [argument.name for argument in get_arguments(base_method)]
        assert argpsec == expected

def _get_method(cls, method_name):
    returned = getattr(cls, method_name)
    return get_underlying_func(returned)
