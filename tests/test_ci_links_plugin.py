# pylint: disable=redefined-outer-name
import itertools
import os
import pytest
import shutil
from slash.plugins import manager

from slash.plugins.builtin.ci_links import Plugin

BUILD_URLS = ('https://jenkins/job/some-job/123/',
              'https://different-jenkins/another-test/9999/')
ENV_VAR_NAMES = ('MY_BUILD_URL_VARIABLE', 'ANOTHER_VARIABLE')
LOG_PATH_TEMPLATES = ('%(build_url)s/%(log_path)s',
                      'https://my-log-storage-server/%(log_path)s')
LOG_DIRS = ('logs_ci_links_plugin_test', os.path.join('some', 'other', 'directory'))


def test_build_url_not_defined(suite):
    manager.install(Plugin(), is_internal=False)
    manager.activate('ci links')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    log_link = result.details.all().get('log_link')
    assert log_link is None


def test_build_url_defined(suite, build_url):
    manager.install(Plugin(), is_internal=False)
    manager.activate('ci links')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    log_link = result.details.all().get('log_link')
    expected_log_link = '/'.join(
        (
            build_url.rstrip('/'),
            'artifact',
            *result.get_log_path().split(os.sep)
        )
    )
    assert log_link == expected_log_link


def test_adds_link_for_passing_test(suite, build_url):
    manager.install(Plugin(), is_internal=False)
    manager.activate('ci links')
    summary = suite.run()
    for test in suite:
        result = summary.get_all_results_for_test(test)[0]
        log_link = result.details.all().get('log_link')
        expected_log_link = '/'.join(
            (
                build_url.rstrip('/'),
                'artifact',
                *result.get_log_path().split(os.sep)
            )
        )
        assert log_link == expected_log_link


def test_nondefault_build_url_environment_variable(
        suite, config_override, build_url_env_var):
    env_var_name, env_var_value = build_url_env_var
    manager.install(Plugin(), is_internal=False)
    config_override(
        'plugin_config.ci_links.build_url_environment_variable',
        env_var_name
    )
    manager.activate('ci links')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    log_link = result.details.all().get('log_link')
    expected_log_link = '/'.join(
        (
            env_var_value.rstrip('/'),
            'artifact',
            *result.get_log_path().split(os.sep)
        )
    )
    assert log_link == expected_log_link


@pytest.mark.parametrize('template', LOG_PATH_TEMPLATES)
def test_nondefault_link_template(
        suite, config_override, build_url, template):
    manager.install(Plugin(), is_internal=False)
    config_override('plugin_config.ci_links.link_template', template)
    manager.activate('ci links')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    log_link = result.details.all().get('log_link')
    local_log_path = '/'.join(result.get_log_path().split(os.sep))
    expected_log_link = template % {'build_url': build_url.rstrip('/'),
                                    'log_path': local_log_path}
    assert log_link == expected_log_link


class PluginWithOverriddenBuildURLGetter(Plugin):

    build_url = 'https://overridden/build/url'

    def _get_build_url(self):
        return self.build_url


def test_overridden_build_url_getter(suite):
    plugin = PluginWithOverriddenBuildURLGetter()
    manager.install(plugin, is_internal=False)
    manager.activate('ci links')
    test = suite.add_test()
    test.when_run.fail()
    summary = suite.run()
    result = summary.get_all_results_for_test(test)[0]
    log_link = result.details.all().get('log_link')
    local_log_path = '/'.join(result.get_log_path().split(os.sep))
    expected_log_link = '%s/artifact/%s' % (plugin.build_url, local_log_path)
    assert log_link == expected_log_link


@pytest.fixture(params=BUILD_URLS)
def build_url(request):
    os.environ['BUILD_URL'] = request.param

    @request.addfinalizer
    def fin():
        os.environ.pop('BUILD_URL')

    return request.param


@pytest.fixture(params=itertools.product(BUILD_URLS, ENV_VAR_NAMES))
def build_url_env_var(request):
    url, env_var_name = request.param
    os.environ[env_var_name] = url

    @request.addfinalizer
    def fin():
        os.environ.pop(env_var_name)

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

    @request.addfinalizer
    def fin():
        shutil.rmtree(os.path.abspath(request.param))
        # shutil.rmtree does not remove the base directory when
        # removing multiple nested directories, so the base
        # directory must be removed separately
        base_dir = request.param.split(os.sep)[0]
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)

    config_override('log.root', request.param)


@pytest.fixture(scope='module', autouse=True)
def deactivate_plugin(request):

    @request.addfinalizer
    def fin():
        manager.deactivate('ci links')

