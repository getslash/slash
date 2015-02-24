from slash.frontend.slash_list import slash_list
from slash._compat import StringIO

import pytest

@pytest.mark.parametrize('flag', ["--only-fixtures", "--only-tests", None])
def test_slash_list(suite, flag):
    suite.debug_info = False
    f = suite.slashconf.add_fixture()
    path = suite.commit()
    report_stream = StringIO()

    args = [path]
    if flag is not None:
        args.append(flag)
    slash_list(args, report_stream)
    assert report_stream.getvalue()


