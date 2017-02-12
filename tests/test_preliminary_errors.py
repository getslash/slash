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


def test_slashrc_errors(suite):
    @suite.slashrc.include
    def __code__():
        1 / 0

    exit_code, output = _console_run(suite)
    assert exit_code != 0
    output = output.lower()
    assert 'unexpected error' in output
    assert 'division' in output
    assert 'zero' in output


@pytest.fixture(params=[
    slash.hooks.session_start,
    slash.hooks.configure,
])
def init_hook(request):
    return request.param


def _console_run(suite):
    suite.disable_debug_info()
    path = suite.commit()
    stream = cStringIO()
    exit_code = slash_run([path], report_stream=stream, working_directory=path)
    return exit_code, stream.getvalue()
