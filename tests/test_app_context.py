import pytest

from slash import get_application_context

from slash.reporting.console_reporter import ConsoleReporter
from slash.reporting.null_reporter import NullReporter


@pytest.mark.parametrize('use_reporter', [True, False])
def test_app_context_reporter(use_reporter):
    with get_application_context(report=use_reporter, argv=[]) as app:
        assert isinstance(app.session.reporter, ConsoleReporter if use_reporter else NullReporter)
