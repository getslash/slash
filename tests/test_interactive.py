import code
import sys

import pytest
import slash
from slash.utils import interactive
from slash import start_interactive_shell


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
