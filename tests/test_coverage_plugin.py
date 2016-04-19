import sys
import pytest

import slash.plugins

@pytest.mark.skipif(hasattr(sys, 'pypy_version_info'), reason='Cannot run on pypy')
def test_coverage_plugin(suite, enabled_coverage_plugin): # pylint: disable=unused-argument
    suite.run()

@pytest.fixture
def enabled_coverage_plugin(request):
    slash.plugins.manager.activate('coverage')

    @request.addfinalizer
    def deactivate(): # pylint: disable=unused-variable
        slash.plugins.manager.deactivate('coverage')
