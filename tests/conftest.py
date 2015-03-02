import itertools
import os
import random
import shutil
import tempfile

from forge import Forge

import gossip
import pytest
import slash
from slash import resuming
from slash.loader import Loader

from .utils.cartesian import Cartesian
from .utils.suite_writer import Suite


@pytest.fixture(scope='session', autouse=True)
def unittest_mode_logging():
    slash.config.root.log.unittest_mode = True


@pytest.fixture(scope='session', autouse=True)
def random_seed():
    random.seed(0xdeadface)


@pytest.fixture(scope='session', autouse=True)
def no_user_config(request):
    tmpdir = tempfile.mkdtemp()
    slash.conf.config.root.run.user_customization_file_path = os.path.join(
        tmpdir, 'slashrc')

    @request.addfinalizer
    def cleanup():
        os.rmdir(tmpdir)


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

_timestamp = itertools.count(1000000)


class Checkpoint(object):

    called = False
    args = kwargs = timestamp = None

    def __call__(self, *args, **kwargs):
        self.called = True
        self.args = args
        self.kwargs = kwargs
        self.timestamp = next(_timestamp)


@pytest.fixture(autouse=True, scope="function")
def fix_resume_path(request):
    prev = resuming._RESUME_DIR
    resuming._RESUME_DIR = tempfile.mkdtemp()

    @request.addfinalizer
    def cleanup():
        shutil.rmtree(resuming._RESUME_DIR)
        resuming._RESUME_DIR = prev


@pytest.fixture
def suite_test(suite, test_type, is_last_test):
    returned = suite.add_test(type=test_type)
    if not is_last_test:
        _ = suite.add_test(type=test_type)

    return returned


@pytest.fixture(params=[True, False])
def is_last_test(request):
    return request.param


@pytest.fixture(params=['method', 'function'])
def test_type(request):
    return request.param


@pytest.fixture
def suite():
    returned = Suite()
    returned.populate()
    return returned


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
