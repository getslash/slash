#pylint: disable=unused-argument, unused-variable
import slash
import gossip
import pytest

from .utils import NamedPlugin, CustomException, raises_maybe, make_runnable_tests


@pytest.mark.parametrize('has_start', [True, False])
def test_plugin_end_not_called_when_start_not_called(gossip_raise_immediately, has_start, checkpoint, restore_plugins_on_cleanup):
    errors = []

    class CustomPlugin(NamedPlugin):
        pass

    class RaisingPlugin(NamedPlugin):
        pass

    if has_start:
        def start(self):
            errors.append('start hook called')
        setattr(CustomPlugin, 'session_start', start)

    def end(self):
        errors.append('end hook called')
    setattr(CustomPlugin, 'session_end', end)

    def do_raise(self):
        checkpoint()
        raise CustomException()
    setattr(RaisingPlugin, 'session_start', do_raise)


    slash.plugins.manager.install(RaisingPlugin(), activate=True)
    slash.plugins.manager.install(CustomPlugin(), activate=True)


    with slash.Session() as s:
        with pytest.raises(CustomException):
            with s.get_started_context():
                def test_something():
                    pass
                slash.runner.run_tests(make_runnable_tests(test_something))

    assert checkpoint.called
    assert not errors


def test_plugin_with_no_session_start_gets_called_session_end(checkpoint):

    @slash.plugins.active
    class MyPlugin(NamedPlugin):

        def session_end(self):
            checkpoint()

    with slash.Session() as s:
        with s.get_started_context():
            pass

    assert checkpoint.called


@pytest.yield_fixture
def gossip_raise_immediately():
    g = gossip.get_group('slash')
    prev = g.get_exception_policy()
    g.set_exception_policy(gossip.RaiseImmediately())
    try:
        yield
    finally:
        g.set_exception_policy(prev)
