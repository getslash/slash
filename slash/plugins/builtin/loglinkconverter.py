import os
from slash.plugins import PluginInterface, parallel_mode


@parallel_mode('child-only')
class Plugin(PluginInterface):
    '''
    Turns the log path included in the additional details for each
    failing test into a web link when running on a CI system by
    prepending the build artifact location onto the log path generated
    by Slash.

    The plugin's default behaviour is compatible with the Jenkins CI
    system, but can be customised by specifying a different environment
    variable for the build URL in
    ``slash.config.plugin_config.loglinkconverter.build_url_environment_variable``,
    (default ``BUILD_URL``), and/or a different link template in
    ``slash.config.plugin_config.loglinkconverter.link_template`` (default
    ``%(build_url)sartifact/%(log_path)s``). The :py:meth:`._get_build_url`
    method can also be overridden to change the way the plugin retrieves
    the build URL.
    '''

    def get_name(self):
        return 'loglinkconverter'

    def get_default_config(self):
        return {
            'build_url_environment_variable': 'BUILD_URL',
            'link_template': '%(build_url)s' + 'artifact/%(log_path)s'
        }

    def _get_build_url(self):
        '''
        Get the URL for the current build. The default implementation
        retrieves the value of the environment variable specified by
        the ``build_url_environment_variable`` plugin configuration
        item. If this function returns ``None``, this plugin will not
        change the log file path.

        .. returns: The URL for the current build, or ``None`` if the
                    current build URL is not set.
        '''
        return os.environ.get(
            self.current_config.build_url_environment_variable)

    def log_file_closed(self, path, result):
        build_url = self._get_build_url()
        if build_url is not None:
            result.set_log_path(
                self.current_config.link_template %
                {'build_url': build_url,
                 'log_path': ("/".join(path.split(os.sep)))}
            )
