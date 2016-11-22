from __future__ import absolute_import

from slash import config as slash_config

from ...utils.conf_utils import Cmdline
from ..interface import PluginInterface

_DATA_FILENAME = '.coverage'

class Plugin(PluginInterface):

    """Enables saving coverage information for test runs
    For more information see https://slash.readthedocs.org/en/master/builtin_plugins.html#coverage
    """

    def get_name(self):
        return "coverage"

    def get_config(self):
        return {
            'config_filename': False // Cmdline(arg='--cov-config'),
            'report_type': 'html' // Cmdline(arg='--cov-report'),
            'report': True,
            'append': False // Cmdline(on='--cov-append'),
            'sources': [] // Cmdline(append='--cov'),
        }

    def activate(self):
        try:
            import coverage
        except ImportError:
            raise RuntimeError('The coverage plugin requires the coverage package to be installed. Please run `pip install coverage` to install it')

        sources = slash_config.root.plugin_config.coverage.sources or None

        self._cov = coverage.Coverage(
            data_file=_DATA_FILENAME,
            config_file=slash_config.root.plugin_config.coverage.config_filename,
            source=sources,
        )
        if slash_config.root.plugin_config.coverage.append:
            self._cov.load()
        self._reporters = []
        for report_type_name in slash_config.root.plugin_config.coverage.report_type.split(','):
            if report_type_name == 'html':
                self._reporters.append(self._cov.html_report)
            elif report_type_name == 'xml':
                self._reporters.append(self._cov.xml_report)
            else:
                raise RuntimeError('Unknown report type: {!r}'.format(report_type_name))
        self._cov.start()


    def session_end(self):
        self._cov.stop()
        self._cov.save()
        if slash_config.root.plugin_config.coverage.report:
            for reporter in self._reporters:
                reporter()
