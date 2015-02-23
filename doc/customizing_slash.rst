.. _customizing:

Customizing and Extending Slash
===============================

This section describes how to tailor Slash to your needs. We'll walk through the process in baby steps, each time adding a small piece of functionality. If you want to start by looking at the finished example, you can skip and see it :ref:`here <finished_example>`.

Customization Basics
--------------------

``.slashrc``
~~~~~~~~~~~~

In order to customize Slash we have to write code that will be executed when Slash loads. Slash offers an easy way to do this -- by placing a file named ``.slashrc`` in your project's root directory. This file is loaded as a regular Python file, so we will write regular Python code in it.

.. note:: The ``.slashrc`` file location is read from the configuration (:ref:`conf.run.project_customization_file_path`). However since it is ready before the command-line parsing phase, it cannot be specified using ``-o``.

Hooks and Plugins
~~~~~~~~~~~~~~~~~

When our ``.slashrc`` file is loaded we have only one shot to install and configure all the customizations we need for the entire session. Slash supports two facilities that can be used together for this task, as we'll see shortly.

*Hooks* are a collection of callbacks that any code can register, thus getting notified when certain events take place. They also support receiving arguments, often detailing what exactly happened.

*Plugins* are a mechanism for loading pieces of code conditionally, and are :ref:`described in detail in the relevant section <plugins>`. For now it is sufficient to say that plugins are classes deriving from :class:`slash.plugins.PluginInterface`, and that can activated upon request. Once activated, methods defined on the plugin which correspond to names of known hooks get registered on those hooks automatically.

1. Customizing Using Plain Hooks
--------------------------------

Our first step is customizing the logging facility to our needs. We are going to implement two requirements:

1. Have logging always turned on in a fixed location (Say ``~/slash_logs``)
2. Collect execution logs at the end of each session, and copy them to a central location (Say ``/remote/path``).

The first requirement is simple - it is done by modifying the global Slash configuration:

.. code-block:: python

		# file: .slashrc
		import os
		import slash

		slash.config.root.log.root = os.path.expanduser('~/slash_logs')

.. note:: Don't be confused about ``slash.config.root.log.root`` above. ``slash.config.root`` is used to access the root of the configuration, while ``log.root`` is the name of the configuration value that controls the log location.

.. seealso:: :ref:`configuration`

The second requirement requires us to do something when the session ends. This is where **hooks** come in. It allows us to register a callback function to be called when the session ends. 

Slash uses `gossip <http://gossip.readthedocs.org>`_ to implement hooks, so we can simply use *gossip.register* to register our callback:

.. code-block:: python

		import gossip
		import shutil

		...
		@gossip.register('slash.session_end')
		def collect_logs():
		    shutil.copytree(...)

Now we need to supply arguments to ``copytree``. We want to copy only the directory of the current session, into a destination directory also specific to this session. How do we do this? The important information can be extracted from :class:`slash.session <slash.core.session.Session>`, which is a proxy to the current object representing the session:

.. code-block:: python

		...
		@gossip.register('slash.session_end')
		def collect_logs():
		    shutil.copytree(
		        slash.session.logging.session_log_path, 
			os.path.join('/remote/path', slash.session.id))

.. seealso:: :ref:`hooks`, :ref:`internals`

2. Organizing Customizations in Plugins
---------------------------------------

Suppose you want to make the log collection behavior optional. Our previous implementation registered the callback immediately, meaning you had no control over whether or not it takes place. Optional customizations are best made optional through organizing them in plugins.

Information on plugins in Slash can be found in :ref:`plugins`, but for now it is enough to mention that plugins are classes deriving from :class:`slash.plugins.PluginInterface`. Plugins can be *installed* and *activated*. Installing a plugin makes it available for activation (but does little else), while activating it actually makes it kick into action. Let's write a plugin that performs the log collection for us:

.. code-block:: python

		...
		class LogCollectionPlugin(slash.plugins.PluginInterface):

		    def get_name(self):
		        return 'logcollector'

		    def session_end(self):
		        shutil.copytree(
		            slash.session.logging.session_log_path, 
			    os.path.join('/remote/path', slash.session.id))

		collector_plugin = LogCollectionPlugin()
		plugins.manager.install(collector_plugin)
		    
The above class inherits from :class:`slash.plugins.PluginInterface` - this is the base class for implementing plugins. We then call :func:`slash.plugins.PluginManager.install` to *install* our plugin. Note that at this point the plugin is not activated.

Once the plugin is installed, you can pass ``--with-logcollector`` to actually activate the plugin. More on that soon.

The ``get_name`` method is required for any plugin you implement for slash, and it should return the name of the plugin. This is where the ``logcollector`` in ``--with-logcollector`` comes from.

The second method, ``session_end``, is the heart of how the plugin works. When a plugin is activated, methods defined on it automatically get registered to the respective hooks with the same name. This means that upon activation of the plugin, our collection code will be called when the session ends..	    

Activating by Default
~~~~~~~~~~~~~~~~~~~~~

In some cases you want to activate the plugin by default, which is easily done with the :func:`slash.plugins.PluginManager.activate`:

.. code-block:: python

		...
		slash.plugins.manager.activate(collector_plugin)

.. note:: You can also just pass ``activate=True`` in the call to ``install``

Once the plugin is enabled by default, you can correspondingly disable it using ``--without-logcollector`` as a parameter to ``slash run``.

.. seealso:: :ref:`plugins`


3. Passing Command-Line Arguments to Plugins
--------------------------------------------

In the real world, you want to test integrated products. These are often physical devices or services running on external machines, sometimes even officially called *devices under test*. We would like to pass the target device IP address as a parameter to our test environment. The easiest way to do this is by writing a plugin that adds command-line options:


.. code-block:: python

		...
		@slash.plugins.active
		class ProductTestingPlugin(slash.plugins.PluginInterface):

		    def get_name(self):
		        return 'your-product'

		    def configure_argument_parser(self, parser):
		        parser.add_argument('-t', '--target', 
			    help='ip address of the target to test')

		    def configure_from_parsed_args(self, args):
		        self.target_address = args.target
			
		    def session_start(self):
		        slash.g.target = Target(self.target_address)


First, we use :func:`slash.plugins.active` decorator here as a shorthand. See :ref:`plugins` for more information.

Second, we use two new plugin methods here - `configure_argument_parser` and `configure_from_parsed_args`. These are called on every activated plugin to give it a chance to control how the commandline is processed. The parser and args passed are the same as if you were using **argparse** directly.

Note that we separate the stages of obtaining the address from actually initializing the target object. This is to postpone the heavier code to the actual beginning of the testing session. The ``session_start`` hook helps us with that - it is called after the argument parsing part.

Another thing to note here is the use of ``slash.g``. This is a convenient location for shared global state in your environment, and is documented in :ref:`global_state`. In short we can conclude with the fact that this object will be available to all test under ``slash.g.target``, as a global setup.

4. Configuration Extensions
---------------------------

Slash supports a hierarchical configuration facility, described in :ref:`the relevant documentation section <configuration>`. In some cases you might want to parametrize your extensions to allow the user to control its behavior. For instance let's add an option to specify a timeout for the target's API:

.. code-block:: python

		...
		@slash.plugins.active
		class ProductTestingPlugin(slash.plugins.PluginInterface):
		    ...
		    def activate(self):
		        slash.config.extend({
			    'product': {
			        'api_timeout_seconds': 50
			    }
			})

		    ...
		    def session_start(self):
		        slash.g.target = Target(
			    self.target_address, 
			    timeout=slash.config.root.product.api_timeout_seconds)
		    

We use the :func:`slash.plugins.PluginInterface.activate` method to control what happens when our plugin is **activated**. Note that this happens very early in the execution phase - even before tests are loaded to be executed.

In the ``activate`` method we use the **extend** capability of Slash's configuration to append configuration paths to it. Then in ``session_start`` we use the value off the configuration to initialize our target.

The user can now easily modify these values from the command-line using the ``-o`` flag to ``slash run``::

  $ slash run ... -o product.api_timeout_seconds=100 ./



Complete Example
----------------

Below is the final code for the ``.slashrc`` file for our project:

.. _finished_example:

.. code-block:: python

        import os
        import shutil
        
        import slash
        
        slash.config.root.log.root = os.path.expanduser('~/slash_logs')
        
        
        @slash.plugins.active
        class LogCollectionPlugin(slash.plugins.PluginInterface):
        
            def get_name(self):
                return 'logcollector'
        
            def session_end(self):
                shutil.copytree(
                    slash.session.logging.session_log_path,
                    os.path.join('/remote/path', slash.session.id))
        
        
        @slash.plugins.active
        class ProductTestingPlugin(slash.plugins.PluginInterface):
        
            def get_name(self):
                return 'your-product'
        
            def activate(self):
                slash.config.extend({
                    'product': {
                        'api_timeout_seconds': 50
                    }
                })
        
            def configure_argument_parser(self, parser):
                parser.add_argument('-t', '--target',
                                    help='ip address of the target to test')
        
            def configure_from_parsed_args(self, args):
                self.target_address = args.target
        
            def session_start(self):
                slash.g.target = Target(
                    self.target_address, timeout=slash.config.root.product.api_timeout_seconds)


