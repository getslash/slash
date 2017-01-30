import pytest

import slash
from slash._compat import cStringIO
from slash.frontend.slash_run import slash_run


def test_errors_during_initialization_hoook(suite, init_hook):

    @init_hook.register
    def callback():
        raise slash.exceptions.SlashException('some error')

    exit_code, output = _console_run(suite)
    assert 'some error' in output
    assert exit_code != 0


@pytest.fixture(params=[
    slash.hooks.session_start,
])
def init_hook(request):
    return request.param


def _console_run(suite):
    suite.disable_debug_info()
    path = suite.commit()
    stream = cStringIO()
    exit_code = slash_run([path], report_stream=stream)
    return exit_code, stream.getvalue()
