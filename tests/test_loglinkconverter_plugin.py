# pylint: disable=redefined-outer-name
import itertools
import os
import pytest
import shutil
from slash.plugins import manager

from slash.plugins.builtin.loglinkconverter import Plugin

BUILD_URLS = ('https://jenkins/job/some-job/123/',
              'https://different-jenkins/another-test/9999/')
ENV_VAR_NAMES = ('MY_BUILD_URL_VARIABLE', 'ANOTHER_VARIABLE')
LOG_PATH_TEMPLATES = ('%(build_url)s/%(log_path)s',
                      'https://my-log-storage-server/%(log_path)s')
LOG_DIRS = ('logs_loglinkconverter_plugin_test', os.path.join('some', 'other', 'directory'))


def test_build_url_not_defined(suite):
    manager.install(Plugin(), is_internal=False)
    manager.activate('loglinkconverter')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    actual_log_path = result.get_log_path()
    expected_log_path = '/'.join(
        (
            os.path.dirname(summary.session.logging.session_log_path),
            result.test_id,
            'debug.log'
        )
    )
    assert actual_log_path == expected_log_path


def test_build_url_defined(suite, build_url):
    manager.install(Plugin(), is_internal=False)
    manager.activate('loglinkconverter')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    actual_log_path = result.get_log_path()
    expected_log_path = '/'.join(
        (
            build_url.rstrip('/'),
            'artifact',
            *os.path.dirname(summary.session.logging.session_log_path).split(os.sep),
            result.test_id,
            'debug.log'
        )
    )
    assert actual_log_path == expected_log_path


def test_nondefault_build_url_environment_variable(
        suite, config_override, build_url_env_var):
    env_var_name, env_var_value = build_url_env_var
    manager.install(Plugin(), is_internal=False)
    config_override(
        'plugin_config.loglinkconverter.build_url_environment_variable',
        env_var_name
    )
    manager.activate('loglinkconverter')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    actual_log_path = result.get_log_path()
    expected_log_path = '/'.join(
        (
            env_var_value.rstrip('/'),
            'artifact',
            *os.path.dirname(summary.session.logging.session_log_path).split(os.sep),
            result.test_id,
            'debug.log'
        )
    )
    assert actual_log_path == expected_log_path


@pytest.mark.parametrize('template', LOG_PATH_TEMPLATES)
def test_nondefault_link_template(
        suite, config_override, build_url, template):
    manager.install(Plugin(), is_internal=False)
    config_override('plugin_config.loglinkconverter.link_template', template)
    manager.activate('loglinkconverter')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    actual_log_path = result.get_log_path()
    local_log_path = '/'.join(
        (
            *os.path.dirname(summary.session.logging.session_log_path).split(os.sep),
            result.test_id,
            'debug.log'
        )
    )
    expected_log_path = template % {'build_url': build_url,
                                    'log_path': local_log_path}
    assert actual_log_path == expected_log_path


class PluginWithOverriddenBuildURLGetter(Plugin):

    build_url = 'https://overridden/build/url/'

    def _get_build_url(self):
        return self.build_url


def test_overridden_build_url_getter(suite):
    plugin = PluginWithOverriddenBuildURLGetter()
    manager.install(plugin, is_internal=False)
    manager.activate('loglinkconverter')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    actual_log_path = result.get_log_path()
    local_log_path = '/'.join(
        (
            *os.path.dirname(summary.session.logging.session_log_path).split(os.sep),
            result.test_id,
            'debug.log'
        )
    )
    expected_log_path = (plugin.build_url +
                         'artifact/%s' % local_log_path)
    assert actual_log_path == expected_log_path


@pytest.fixture(params=BUILD_URLS)
def build_url(request):
    os.environ['BUILD_URL'] = request.param

    def fin():
        os.environ.pop('BUILD_URL')

    request.addfinalizer(fin)

    return request.param


@pytest.fixture(params=itertools.product(BUILD_URLS, ENV_VAR_NAMES))
def build_url_env_var(request):
    url, env_var_name = request.param
    os.environ[env_var_name] = url

    def fin():
        os.environ.pop(env_var_name)

    request.addfinalizer(fin)

    return env_var_name, url


@pytest.fixture(params=LOG_DIRS, autouse=True)
def log_dir(request, config_override):
    '''
    Create a temporary log directory relative to the working directory.
    This is used instead of the pytest built-in 'tmpdir' because
    'tmpdir' has an absolute path, and this plugin will not work with
    absolute log paths.
    '''
    os.makedirs(request.param)

    def fin():
        shutil.rmtree(os.path.abspath(request.param))
        # shutil.rmtree does not remove the base directory when
        # removing multiple nested directories, so the base
        # directory must be removed separately
        base_dir = request.param.split(os.sep)[0]
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)

    request.addfinalizer(fin)

    config_override('log.root', request.param)
