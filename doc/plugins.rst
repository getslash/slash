.. _plugins:

Plugins
=======

Plugins are a comfortable way of extending Slash's behavior. They are objects inheriting from a :class:`common base class <.PluginInterface>` that can be activated to modify or what happens in select point of the infrastructure. 

The Plugin Interface
--------------------

Plugins have several special methods that can be overriden, like :func:`get_name <slash.plugins.PluginInterface.get_name>` or :func:`configure_argument_parser <slash.plugins.PluginInterface.configure_argument_parser>`. Except for these methods and the ones documented, each public method (i.e. a method not beginning with an underscore) must correspond to a :ref:`slash hook <hooks>` by name. 

The name of the plugin should be returned by :func:`get_name <slash.plugins.PluginInterface.get_name>`. This name should be unique, and not shared by any other plugin.

Plugin Discovery
----------------

Plugins can be loaded from multiple locations. 

Search Paths
~~~~~~~~~~~~

First, the paths in ``plugins.search_paths`` are searched for python files. For each file, a function called ``install_plugins`` is called (assuming it exists), and this gives the file a chance to install its plugins.

*TODO* more ways of installing.

Plugin Installation
-------------------

To install a plugin, use the :func:`slash.plugins.manager.install <slash.plugins.PluginManager.install>` function, and pass it the plugin class that is being installed. Note that installed plugins are not active by default, and need to be explicitly activated (see below).

Only plugins that are :class:`.PluginInterface` derivative instances are accepted.

To uninstall plugins, you can use the :func:`slash.plugins.manager.uninstall <slash.plugins.PluginManager.uninstall>`. 

.. note:: uninstalling plugins also deactivates them.


Plugin Activation
-----------------

Plugins are activated via :func:`slash.plugins.manager.activate <slash.plugins.PluginManager.activate>` and deactivated via :func:`slash.plugins.manager.deactivate <slash.plugins.PluginManager.deactivate>`.

During the activation all hook methods get registered to their respective hooks, so any plugin containing an unknown hook will trigger an exception.

.. note:: by default, all method names in a plugin are assumed to belong to the *slash* gossip group. This means that the method ``session_start`` will register on ``slash.session_start``. You can override this behavior by using :func:`slash.plugins.registers_on`:
  
  .. code-block:: python

     from slash.plugins import registers_on
     
     class MyPlugin(PluginInterface):
         @registers_on('some_hook')
         def func(self):
             ...


``registers_on(None)`` has a special meaning - letting Slash know that this is not a hook entry point, but a private method belonging to the plugin class itself.

.. seealso:: :ref:`hooks`


Activating plugins from command-line is usually done with the ``--with-`` prefix. For example, to activate a plugin called ``test-plugin``, you can pass ``--with-test-plugin`` when running ``slash run``. 

Also, since some plugins can be activated from other locations, you can also override and deactivate plugins using ``--without-X`` (e.g. ``--without-test-plugin``).

Conditionally Registering Hooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can make the hook registration of a plugin *conditional*, meaning it should only happen if a boolean condition is ``True``.

This can be used to create plugins that are compatible with multiple versions of Slash:

.. code-block:: python
       
       class MyPlugin(PluginInterface):
           ...
           @slash.plugins.register_if(int(slash.__version__.split('.')[0]) >= 1)
           def shiny_new_hook(self):
	       ...

.. seealso:: :func:`slash.plugins.register_if`

Plugin Command-Line Interaction
-------------------------------

In many cases you would like to receive options from the command line. Plugins can implement the :func:`configure_argument_parser <slash.plugins.PluginInterface.configure_argument_parser>` and the :func:`configure_parsed_args <slash.plugins.PluginInterface.configure_from_parsed_args>` functions:

.. code-block:: python

 class ResultsReportingPlugin(PluginInterface):
 
     def configure_argument_parser(self, parser):
         parser.add_argument("--output-filename", help="File to write results to")
 
     def configure_from_parsed_args(self, args):
         self.output_filename = args.output_filename

Plugin Configuration
--------------------

Plugins can expose the :func:`config <slash.plugins.PluginInterface.get_config>` can provide configuration to be placed under ``plugin_config.<plugin name>``:

.. code-block:: python

 class LogCollectionPlugin(PluginInterface):

     def get_config(self):
         return {
             'log_destination': '/some/default/path'
         }


Plugin Examples
---------------

An example of a functioning plugin can be found in the :ref:`customizing` section.

Errors in Plugins
-----------------

As more logic is added into plugins it becomes more likely for exceptions to occur when running their logic. As seen above, most of what plugins do is done by registering callbacks onto hooks. Any exception that escapes these registered functions will be handled the same way any exception in a hook function is handled, and this depends on the current exception swallowing configuration.

.. seealso:: 

   * :ref:`exception swallowing <exception_swallowing>`
   * :ref:`hooks documentation <hooks>`


Plugin Dependencies
-------------------

You can manage plugin dependencies through the `gossip dependency mechanism <http://gossip.readthedocs.org/en/latest/hook_dependencies.html>`_. The easiest way is using the needs/provides model, also supported by Slash plugins.

The idea is to have plugins specify what they need and what they provide in terms of tokens (basically arbitrary strings that have a meaning to the reader). Slash, by using *gossip* will take care of the invocation order to preserve the constraint:


.. code-block:: python
       
       class TestIdentificationPlugin(PluginInterface):

           @slash.plugins.provides('awesome_test_id')
           def test_start(self):
	       slash.context.test.awesome_test_id = awesome_id_allocation_service()

       class TestIdentificationLoggingPlugin(PluginInterface):

           @slash.plugins.needs('awesome_test_id')
           def test_start(self):
	       slash.logger.debug('Test has started with the awesome id of {!r}', slash.context.test.awesome_id)


.. note:: The ``@slash.plugins.needs`` / ``@slash.plugins.provides`` decorators can also be specified on the plugin class itself, automatically marking all hook methods


Plugin Manager
--------------

As mentioned above, the Plugin Manager provides API to activate (or deacativate) and install (or uninstall) plugins.
Additionally, it provides access to instances of registered plugins by their name via :func:`slash.plugins.manager.get_plugin <slash.plugins.PluginManager.get_plugin>`.
This could be used to access plugin attributes whose modification (e.g. by fixtures) can alter the plugin's behavior.
