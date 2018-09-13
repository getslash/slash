from slash.app import Application
from slash import hooks

from slash.reporting.console_reporter import ConsoleReporter


def test_app_reporter(checkpoint):
    hooks.app_quit.register(checkpoint) # pylint: disable=no-member
    with Application() as app:
        assert isinstance(app.session.reporter, ConsoleReporter)
        assert not checkpoint.called
    assert checkpoint.called


def test_custom_reporter():

    class DummyReporter(object):
        pass

    dummy_reporter = DummyReporter()

    app = Application()
    app.set_reporter(dummy_reporter)
    with app:
        assert app.session.reporter is dummy_reporter
