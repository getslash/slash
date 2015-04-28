import abc

class PluginInterface(object):
    """
    This class represents the base interface needed from plugin classes.
    """
    __metaclass__ = abc.ABCMeta

    def activate(self):
        """
        Called when the plugin is activated
        """
        pass

    def get_config(self):
        """
        Optional: should return a dictionary or a confetti object which will be placed under
        ``slash.config.plugin_config.<plugin_name>``
        """
        pass

    def deactivate(self):
        """
        Called when the plugin is deactivated

        .. note:: this method might not be called in practice, since it is not guaranteed that plugins are always
          deactivated upon process termination. The intention here is to make plugins friendlier to cases
          in which multiple sessions get established one after another, each with a different set of plugins.
        """
        pass

    def configure_argument_parser(self, parser):
        """
        Gives a chance to the plugin to add options received from command-line
        """
        pass

    def configure_from_parsed_args(self, args):
        """
        Called after successful parsing of command-line arguments
        """
        pass

    def get_description(self):
        """
        Retrieves a quick description for this plugin, mostly used in command-line help or online documentation.
        It is not mandatory to override this method.
        """
        return None

    def get_name(self):
        """
        Returns the name of the plugin class. This name is used to register, disable and address
        the plugin during runtime.

        Note that the command-line switches (``--with-...``) are derived from this name.

        Any implemented plugin must override this method.
        """
        raise NotImplementedError() # pragma: no cover
