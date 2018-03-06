# pylint: disable=redefined-outer-name
import itertools
import os
import random
import tempfile
from uuid import uuid4

from forge import Forge

import gossip
import pytest
import slash
import slash.plugins
from slash.loader import Loader
from slash.core.result import GlobalResult, Result

from .utils.cartesian import Cartesian
from .utils.suite_writer import Suite
from .utils.suite_builder import SuiteBuilder
from .utils.garbage_collection import GarbageCollectionMarker


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
    def cleanup():  # pylint: disable=unused-variable
        os.rmdir(tmpdir)


@pytest.fixture
def no_plugins(request):
    slash.plugins.manager.uninstall_all()
    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        slash.plugins.manager.uninstall_all()
        slash.plugins.manager.install_builtin_plugins()


@pytest.fixture
def forge(request):

    returned = Forge()

    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        returned.verify()
        returned.restore_all_replacements()

    return returned


@pytest.fixture
def config_override(request):

    def _override(path, value):
        prev_value = slash.config.get_config(path).get_value()

        @request.addfinalizer
        def restore():  # pylint: disable=unused-variable
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


@pytest.fixture
def checkpoint():
    return Checkpoint()

@pytest.fixture
def checkpoint1():
    return Checkpoint()

@pytest.fixture
def checkpoint2():
    return Checkpoint()


_timestamp = itertools.count(1000000)


class Checkpoint(object):

    called_count = 0
    args = kwargs = timestamp = None

    def __call__(self, *args, **kwargs):
        self.called_count += 1
        self.args = args
        self.kwargs = kwargs
        self.timestamp = next(_timestamp)

    @property
    def called(self):
        return self.called_count > 0

@pytest.fixture
def suite_test(suite, test_type, is_last_test):
    returned = suite.add_test(type=test_type)
    if not is_last_test:
        _ = suite.add_test(type=test_type)

    return returned

@pytest.fixture
def last_suite_test(suite, test_type):
    return suite.add_test(type=test_type)

@pytest.fixture(params=[GlobalResult, Result])
def result(request):
    return request.param()


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
def suite_builder(tmpdir):
    return SuiteBuilder(str(tmpdir.join('suite_builder')))


@pytest.fixture
def parallel_suite_test(parallel_suite, test_type, is_last_test):
    returned = parallel_suite.add_test(type=test_type)
    if not is_last_test:
        _ = parallel_suite.add_test(type=test_type)

    return returned


@pytest.fixture
def parallel_suite():
    returned = Suite(debug_info=False, is_parallel=True)
    returned.populate()
    return returned

@pytest.fixture
def runnable_test_dir(tmpdir):
    tests_dir = tmpdir.join(str(uuid4()))
    filename = str(uuid4()).replace('-', '') + '.py'
    with tests_dir.join(filename).open('w', ensure=True) as f:
        f.write('def test_something():\n    pass')
    return tests_dir

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
    def finalize():  # pylint: disable=unused-variable
        returned.__exit__(None, None, None)

    return returned


@pytest.fixture(params=["slashconf", "module"])
def defined_fixture(request, suite, suite_test):
    if request.param == 'slashconf':
        return suite.slashconf.add_fixture()
    elif request.param == 'module':
        return suite_test.file.add_fixture()

    raise NotImplementedError()  # pragma: no cover


@pytest.fixture
def gc_marker():
    return GarbageCollectionMarker()


@pytest.fixture(autouse=True, scope="function")
def reset_gossip(request):
    @request.addfinalizer
    def cleanup():  # pylint: disable=unused-variable
        for group in list(gossip.get_groups()):
            if group.name == 'slash':
                continue
            group.undefine()

        for hook in gossip.get_all_hooks():
            if hook.group.name != 'slash':
                hook.undefine()
            else:
                hook.unregister_all()


@pytest.fixture  # pylint: disable=unused-argument
def plugin(no_plugins):  # pylint: disable=unused-argument

    class StartSessionPlugin(slash.plugins.PluginInterface):
        _activate_called = False
        _deactivate_called = False

        def __init__(self):
            super(StartSessionPlugin, self).__init__()
            self.session_start_call_count = 0

        def get_name(self):
            return "start-session"

        def session_start(self):
            self.session_start_call_count += 1

        def activate(self):
            self._activate_called = True

        def deactivate(self):
            self._deactivate_called = True
    return StartSessionPlugin()


@pytest.fixture(params=['slashconf', 'file'])
def get_fixture_location(request):

    def getter(test):
        if request.param == 'slashconf':
            return test.suite.slashconf
        elif request.param == 'file':
            return test.file
        else:
            raise NotImplementedError() # pragma: no cover
    return getter

@pytest.fixture
def restore_plugins_on_cleanup(request):
    request.addfinalizer(slash.plugins.manager.install_builtin_plugins)
    request.addfinalizer(slash.plugins.manager.uninstall_all)


@pytest.fixture
def logs_dir(config_override, tmpdir, relative_symlinks):
    returned = tmpdir.join('logs')
    config_override("log.root", str(returned.join("files")))
    config_override("log.last_session_symlink",
                    str("../links/last-session" if relative_symlinks else returned.join("links", "last-session")))
    config_override("log.last_session_dir_symlink",
                    str("../links/last-session-dir" if relative_symlinks else returned.join("links", "last-session-dir")))
    config_override("log.last_test_symlink",
                    str("../links/last-test" if relative_symlinks else returned.join("links", "last-test")))
    config_override("log.last_failed_symlink",
                    str("../links/last-failed" if relative_symlinks else returned.join("links", "last-failed")))

    return returned


@pytest.fixture(params=[True, False])
def relative_symlinks(request):
    return request.param


@pytest.fixture
def session_log(logs_dir):
    return logs_dir.join('links').join('last-session')


@pytest.fixture
def unique_string1():
    return str(uuid4())


@pytest.fixture(params=[True, False])
def yield_fixture_decorator(request):
    should_use_explicitly = request.param
    if should_use_explicitly:
        return slash.yield_fixture
    return slash.fixture


@pytest.fixture  # pylint: disable=unused-argument
def xunit_filename(tmpdir, request, config_override):  # pylint: disable=unused-argument
    xunit_filename = str(tmpdir.join('xunit.xml'))
    slash.plugins.manager.activate('xunit')

    slash.config.root.plugin_config.xunit.filename = xunit_filename

    @request.addfinalizer
    def deactivate():  # pylint: disable=unused-variable
        slash.plugins.manager.deactivate('xunit')

    return xunit_filename
