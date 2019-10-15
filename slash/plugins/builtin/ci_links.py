import os
from slash.plugins import PluginInterface, parallel_mode
from slash import context


@parallel_mode('child-only')
class Plugin(PluginInterface):
    '''
    Adds a web link to the test log file artifact archived by a
    continuous integration (CI) system to the test's 'additional details'
    store. This creates a link to the test log file for each failing test
    in the test summary view, and also adds the link to each test's
    additional details table in the Backslash web interface.

    .. note:: This behaviour only occurs if the build URL is defined.

    The plugin defaults to retrieving the build URL from the ``BUILD_URL``
    environment variable populated by the Jenkins CI system, but this can
    be customised by specifying a different environment variable in
    ``slash.config.root.plugin_config.ci_links.build_url_environment_variable``.
    It can also be customised by overriding the :py:meth:`._get_build_url`
    method in a subclass. The default format string used to generate the
    link is ``%(build_url)s/artifact/%(log_path)s``, but this can be
    customised by specifying a different template in
    ``slash.config.root.plugin_config.ci_links.link_template``.
    '''

    def get_name(self):
        return 'ci links'

    def get_default_config(self):
        return {
            'build_url_environment_variable': 'BUILD_URL',
            'link_template': '%(build_url)s/artifact/%(log_path)s'
        }

    def _get_build_url(self):
        '''
        Get the URL for the current build. The default implementation
        retrieves the value of the environment variable specified by
        the ``build_url_environment_variable`` plugin configuration
        item. If this function returns ``None``, this plugin will not
        change the log file path.

        .. returns: The URL for the current build (with any trailing '/'
                    character stripped), or ``None`` if the
                    current build URL is not set.
        '''
        retval = os.environ.get(
            self.current_config.build_url_environment_variable)
        if retval is not None:
            retval = retval.rstrip('/')
        return retval

    def test_end(self):
        build_url = self._get_build_url()
        if build_url is not None:
            local_path = context.result.get_log_path()
            context.result.details.set(
                'log_link',
                self.current_config.link_template %
                {'build_url': build_url,
                 'log_path': '/'.join(local_path.split(os.sep))}
            )
