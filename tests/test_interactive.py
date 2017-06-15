# pylint: disable=redefined-outer-name
from munch import Munch
import pytest
import slash
from slash.utils import interactive
from slash import start_interactive_shell


def test_interactive_test(suite, interactive_checkpoint):

    summary = suite.run(additional_args=['-i'])
    assert interactive_checkpoint.called

    result = next(summary.session.results.iter_test_results())
    assert repr(result.test_metadata) == '<Interactive>'
    assert result.test_metadata.file_path == '<Interactive>'


@pytest.mark.parametrize('with_session', [True, False])
def test_interactive_scope(forge, with_session):
    interact_mock = forge.replace(interactive, '_interact')

    interact_mock({'x': 2, 'y': 3})
    forge.replay()

    if with_session:
        with slash.Session():
            slash.g.x = 2
            start_interactive_shell(y=3)
    else:
        start_interactive_shell(x=2, y=3)


def test_interactive_planned_tests(interactive_checkpoint, suite):

    counts = Munch(original=len(suite), got=None)

    @slash.hooks.register
    def tests_loaded(tests):    # pylint: disable=unused-variable
        counts.got = len(tests)

    suite.run(additional_args=['-i'])
    assert interactive_checkpoint.called
    assert counts.got == counts.original + 1



@pytest.fixture
def interactive_checkpoint(checkpoint, forge):
    def _interact(*_, **__):  # pylint: disable=unused-argument
        assert slash.context.session.scope_manager.get_current_stack() == ['session', 'module', 'test']
        assert slash.context.test.__slash__.is_interactive()
        assert slash.context.test.__slash__.id
        checkpoint()

    forge.replace_with(interactive, '_interact', _interact)

    return checkpoint
