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


def test_exception_during_app_exit_debugger(checkpoint, config_override):
    @hooks.entering_debugger.register  # pylint: disable=no-member
    def callback(*_, **__):  # pylint: disable=unused-variable
        checkpoint()
        raise Exception('Entering debugger error')
    config_override('debug.enabled', True)
    with Application() as app:
        raise Exception('Some Exception')
    assert checkpoint
    assert app.exit_code != 0
    assert checkpoint.called_count == 1
