import pytest


def test_plugin_activation_forcing_via_activate(customized_suite, suite_test):

    @customized_suite.slashrc.include
    def __code__():
        slash.plugins.manager.activate('custom')

    result = customized_suite.run().session.results.global_result
    assert result.data['customized']


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
