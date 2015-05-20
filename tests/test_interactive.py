import code
import sys

import pytest
import slash
from slash.utils import interactive
from slash import start_interactive_shell


def test_interactive_test(forge, suite, checkpoint):

    def _interact(*_, **__):
        assert slash.context.session.scope_manager.get_current_stack() == ['session', 'module', 'test']
        checkpoint()

    forge.replace_with(interactive, '_interact', _interact)

    summary = suite.run(additional_args=['-i'])
    assert checkpoint.called

    result = next(summary.session.results.iter_test_results())
    assert repr(result.test_metadata) == '<Interactive>'


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
