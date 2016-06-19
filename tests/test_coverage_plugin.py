import sys
import pytest
import coverage

import slash.plugins

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'), reason='Cannot run on pypy')
def test_coverage_plugin(suite, enabled_coverage_plugin): # pylint: disable=unused-argument
    suite.run()

@pytest.fixture
def enabled_coverage_plugin(request, patched_coverage, config_override):
    slash.plugins.manager.activate('coverage')
    config_override('plugin_config.coverage.report', False)

    @request.addfinalizer
    def deactivate(): # pylint: disable=unused-variable
        slash.plugins.manager.deactivate('coverage')

@pytest.yield_fixture
def patched_coverage(forge):
    s = forge.replace_with(coverage.Coverage, 'start', lambda self: None)
    forge.replay()
    try:
        yield
    finally:
        forge.restore_all_replacements()
