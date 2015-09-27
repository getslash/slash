import pytest


def test_plugin_activation_forcing_via_activate(customized_suite, suite_test):

    @customized_suite.slashrc.include
    def __code__():
        slash.plugins.manager.activate('custom')

    result = customized_suite.run().session.results.global_result
    assert result.data['customized']


def test_plugin_activation_deactivate_via_commandline(customized_suite, suite_test):

    @customized_suite.slashrc.include
    def __code__():
        slash.plugins.manager.activate_later('custom')

    result = customized_suite.run(additional_args=['--without-custom']).session.results.global_result
    assert 'customized' not in result.data


def test_plugin_activation_from_configure_hook(customized_suite, suite_test):

    @customized_suite.slashrc.include
    def __code__():
        @slash.hooks.configure.register
        def configure_hook():
            slash.plugins.manager.activate_later('custom')

    result = customized_suite.run().session.results.global_result
    assert 'customized' in result.data


def test_plugin_deactivation_override_configure_hook(customized_suite, suite_test):

    @customized_suite.slashrc.include
    def __code__():
        @slash.hooks.configure.register
        def configure_hook():
            slash.plugins.manager.activate_later('custom')

    result = customized_suite.run(additional_args=['--without-custom']).session.results.global_result
    assert 'customized' not in result.data

def test_configure_hook_depends_on_configuration_cmdline(customized_suite, suite_test):

    @customized_suite.slashrc.include
    def __code__():
        slash.config.extend({
            'some_config': 1 // slash.conf.Cmdline(arg='--some-config'),
        })

        @slash.hooks.configure.register
        def configure_hook():
            assert slash.config.root.some_config == 1000

    result = customized_suite.run(additional_args=['--some-config=1000']).session.results.global_result


@pytest.fixture
def customized_suite(suite):

    @suite.slashrc.include
    def __code__():
        class CustomPlugin(slash.plugins.PluginInterface):

            def get_name(self):
                return 'custom'

            def session_start(self):
                slash.session.results.global_result.data['customized'] = True
        slash.plugins.manager.install(CustomPlugin())

    return suite
