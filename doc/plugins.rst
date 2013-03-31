Plugins
=======

Plugins are a comfortable way of extending Shakedown's behavior. They are objects inheriting from a :class:`common base class <.PluginInterface>` that can be activated to modify or what happens in select point of the infrastructure. 

*TODO*: describe fixture setup using plugins

The Plugin Interface
--------------------

Plugins have several special methods that can be overriden, like :func:`.PluginInterface.get_name` or :func:`.PluginInterface.configure_arg_parser`. Except for these methods and the ones documented, each public method (i.e. a method not beginning with an underscore) must correspond to a :ref:`shakedown hook <hooks>` by name. 

The name of the plugin should be returned by :func:`.PluginInterface.get_name`. This name should be unique, and not shared by any other plugin.

.. autoclass:: shakedown.plugins.interface.PluginInterface

Plugin Discovery
----------------

Plugins can be loaded from multiple locations. 

Search Paths
~~~~~~~~~~~~

First, the paths in ``plugins.search_paths`` are searched for python files. For each file, a function called ``install_plugins`` is called (assuming it exists), and this gives the file a chance to install its plugins.

*TODO* more ways of installing.

Plugin Installation
-------------------

To install a plugin, use the :func:`shakedown.plugins.manager.install <.plugins.PluginManager.install>` function, and pass it the plugin class that is being installed. Note that installed plugins are not active by default, and need to be explicitly activated (see below).

Only plugins that are :class:`.PluginInterface` derivative instances are accepted.

To uninstall plugins, you can use the :func:`shakedown.plugins.manager.uninstall <.plugins.PluginManager.uninstall>`. 

.. note:: uninstalling plugins also deactivates them.


Plugin Activation
-----------------

Plugins are activated via :func:`shakedown.plugins.manager.activate <.plugins.PluginManager.activate>`. During the activation all hook methods get registered to their respective hooks, so any plugin containing an unknown hook will trigger an exception.

Activating plugins from command-line is usually done with the ``--with-`` prefix. For example, to activate a plugin called ``test-plugin``, you can pass ``--with-test-plugin`` when running ``shake run``. 

Also, since some plugins can be activated from other locations, you can also override and deactivate plugins using ``--without-X`` (e.g. ``--without-test-plugin``).

Plugin Command-Line Interaction
-------------------------------

In many cases you would like to receive options from the command line. Plugins can implement the :func:`.PluginInterface.configure_arg_parser` and the :func:`.PluginInterface.configure_parsed_args` functions:

.. code-block:: python

 class ResultsReportingPlugin(PluginInterface):
     def configure_arg_parser(self, parser):
         parser.add_argument("--output-filename", help="File to write results to")
     def configure_parsed_args(self, args):
         self.output_filename = args.output_filename

Errors in Plugins
-----------------

Since plugins use hooks to achieve their functionality, the same rules of exception swallowing apply to them as well. See :ref:`exception swallowing <exception_swallowing>` and :ref:`the hook documentation <hooks>` for more information.

The PluginInterface Class
-------------------------

.. autoclass:: shakedown.plugins.PluginManager
