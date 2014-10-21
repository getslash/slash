import shutil
import tempfile

import logbook.compat

from forge import Forge
import gossip
import pytest
import slash
from slash import resuming
from slash.loader import Loader

from .utils.suite import TestSuite
from .utils.cartesian import Cartesian

import random

@pytest.fixture(scope='session', autouse=True)
def random_seed():
    random.seed(0xdeadface)


@pytest.fixture
def forge(request):

    returned = Forge()

    @request.addfinalizer
    def cleanup():
        returned.verify()
        returned.restore_all_replacements()

    return returned


@pytest.fixture
def config_override(request):

    def _override(path, value):
        prev_value = slash.config.get_config(path).get_value()

        @request.addfinalizer
        def restore():
            slash.config.assign_path(path, prev_value)
        slash.config.assign_path(path, value)
    return _override


@pytest.fixture
def cartesian():
    return Cartesian()


@pytest.fixture(scope="function", autouse=True)
def cleanup_hook_registrations(request):
    @request.addfinalizer
    def _cleanup():
        for hook in gossip.get_group("slash").get_hooks():
            hook.unregister_all()
        assert not gossip.get_group("slash").get_subgroups()


@pytest.fixture(scope="function")
def checkpoint():
    return Checkpoint()


class Checkpoint(object):

    called = False

    def __call__(self, *args, **kwargs):
        self.called = True


@pytest.fixture(autouse=True, scope="function")
def fix_resume_path(request):
    prev = resuming._RESUME_DIR
    resuming._RESUME_DIR = tempfile.mkdtemp()

    @request.addfinalizer
    def cleanup():
        shutil.rmtree(resuming._RESUME_DIR)
        resuming._RESUME_DIR = prev


@pytest.fixture
def suite_test(populated_suite, test_factory, is_last_test):
    returned = test_factory(populated_suite)
    if not is_last_test:
        _ = test_factory(populated_suite)

    return returned


@pytest.fixture(params=[True, False])
def is_last_test(request):
    return request.param


def _create_regular_test_function(suite):
    return suite.add_test(regular_function=True)


def _create_test_method(suite):
    return suite.add_test(regular_function=False)


@pytest.fixture(params=[_create_regular_test_function,
                        _create_test_method])
def test_factory(request):
    return request.param


@pytest.fixture(scope='function')
def populated_suite(suite):
    suite.populate()
    return suite


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
