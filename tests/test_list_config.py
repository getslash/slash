import subprocess
import sys

import munch
import pytest
from slash.frontend.list_config import list_config
from io import StringIO


def test_slash_list_config():
    report_stream = StringIO()
    list_config(munch.Munch(argv=[]), report_stream)
    assert report_stream.getvalue()


def test_slash_list_config_with_filters():
    report_stream = StringIO()
    list_config(munch.Munch(argv=["log"]), report_stream)
    assert "log.root" in report_stream.getvalue()


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def test_slash_list_config_closed_stdout_pipe():
    # e.g. ``slash list-config | head -1``: the reader goes away before we are done writing
    proc = subprocess.Popen(
        [sys.executable, "-m", "slash.frontend.main", "list-config"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.stdout.close()
    stderr = proc.stderr.read().decode()
    proc.stderr.close()
    proc.wait()
    assert "BrokenPipeError" not in stderr
    assert "Traceback" not in stderr
