import pytest
from slash import Session
from slash.loader import Loader
from slash.exceptions import CannotLoadTests


def test_import_error_registers_as_session_error(active_slash_session, test_loader):
    with pytest.raises(CannotLoadTests):
        test_loader.get_runnables(["/non/existent/path"])
    errors = active_slash_session.results.global_result.get_errors()
    assert len(errors) == 1
    [error] = errors


def test_import_errors_without_session(unloadable_suite):

    with pytest.raises(CannotLoadTests):
        Loader().get_runnables([unloadable_suite.path])


def test_import_errors_with_session(unloadable_suite):
    with Session() as s:
        tests = Loader().get_runnables(unloadable_suite.path)

    assert tests
    [err] = s.results.global_result.get_errors()
    assert 'No module named nonexistent' in err.message


@pytest.fixture
def unloadable_suite(suite):
    suite.populate()

    suite.files[2].inject_line('from nonexistent import nonexistent')

    suite.commit()
    return suite
