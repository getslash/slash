import os
from slash.plugins import PluginInterface, parallel_mode
from slash import context


@parallel_mode('child-only')
class Plugin(PluginInterface):
    '''
    For more information see https://slash.readthedocs.org/en/master/builtin_plugins.html#linking-to-logs-archived-by-a-ci-system
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
        Get the URL for the current build.

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
