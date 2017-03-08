# pylint: disable=redefined-outer-name,unused-argument
import sys
import pytest
import coverage

import slash.plugins


@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'), reason='Cannot run on pypy')
def test_coverage_plugin(suite, enabled_coverage_plugin, config_override, report_type):
    config_override('plugin_config.coverage.report', True)
    config_override('plugin_config.coverage.report_type', report_type)
    suite.run()

def test_invalid_report_type(config_override):
    config_override('plugin_config.coverage.report_type', 'bla')
    with pytest.raises(RuntimeError) as exc:
        slash.plugins.manager.activate('coverage')
    assert 'Unknown report type' in str(exc.value)


@pytest.fixture
def enabled_coverage_plugin(request, patched_coverage, config_override, should_append, report_type):
    config_override('plugin_config.coverage.report', False)
    config_override('plugin_config.coverage.append', should_append)
    config_override('plugin_config.coverage.report_type', report_type)
    slash.plugins.manager.activate('coverage')

    @request.addfinalizer
    def deactivate():  # pylint: disable=unused-variable
        slash.plugins.manager.deactivate('coverage')


@pytest.fixture(params=[True, False])
def should_append(request):
    return request.param


@pytest.fixture(params=['html', 'xml', 'html,xml'])
def report_type(request):
    return request.param


@pytest.yield_fixture
def patched_coverage(forge):
    forge.replace_with(coverage.Coverage, 'start', lambda self: None)
    forge.replay()
    try:
        yield
    finally:
        forge.restore_all_replacements()
