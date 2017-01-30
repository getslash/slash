from slash.app import Application

from slash.reporting.console_reporter import ConsoleReporter


def test_app_reporter():
    with Application() as app:
        assert isinstance(app.session.reporter, ConsoleReporter)
