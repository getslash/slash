import shutil
import tempfile

import logbook.compat

import pytest
import slash
from slash import resuming
from slash.loader import Loader

from .utils.suite import TestSuite


@pytest.fixture(autouse=True, scope="function")
def fix_resume_path(request):
    prev = resuming._RESUME_DIR
    resuming._RESUME_DIR = tempfile.mkdtemp()

    @request.addfinalizer
    def cleanup():
        shutil.rmtree(resuming._RESUME_DIR)
        resuming._RESUME_DIR = prev

@pytest.fixture(scope="function")
def suite(request):
    returned = TestSuite()
    request.addfinalizer(returned.cleanup)
    return returned

@pytest.fixture
def setup_logging(request):
    logbook.compat.LoggingHandler().push_application()

@pytest.fixture
def slash_session():
    return slash.Session()

@pytest.fixture
def test_loader():
    return Loader()

@pytest.fixture
def active_slash_session(request):
    returned = slash.Session()
    returned.__enter__()

    @request.addfinalizer
    def finalize():
        returned.__exit__(None, None, None)

    return returned
