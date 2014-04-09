Hooks
=====

.. _hooks: 

Registering Hooks
-----------------

You can add callbacks to be called in various points of Slash's execution via the hook mechanism. Registering callbacks to hooks can be done via the :func:`.Callback.register` method, which can also be used as a decorator:

.. code-block:: python

    import slash
    
    @slash.hooks.session_start.register
    def handler():
        print("Session has started: ", slash.context.session)

Hook Errors
-----------

Since hooks are rarely related to each other, an error in a hook callback does not terminate the call chain, and is swallowed while issuing a warning. The :ref:`conf.hooks.swallow_exceptions` configuration options controls this behavior. When disabled, exceptions will be propagated after all hooks are called. The first encountered exception will be the one raised eventually.

This mechanism makes use of the :ref:`exception_swallowing` mechanism of Slash, so you can bypass it in several ways if you want. See :ref:`the exception swallowing documentation <exception_swallowing>` for more details.

**TODO: sentry support and debuggability**

Available Hooks
---------------

The following hooks are available from the ``slash.hooks`` module:

.. hook_list_doc::

Advanced Usage
--------------

Adding Custom Hooks
~~~~~~~~~~~~~~~~~~~

In some cases you want to add custom hooks to Slash. Let's assume, for example, that we are testing the `our microwave <building_solution>`_ and we would like to support a hook that is called when the microwave is shut down. To add the ``microwave_shutdown`` hook we can just call:

.. code-block:: python

  import slash
  slash.hooks.ensure_custom_hook("microwave_shutdown")

  ...

  @slash.hooks.microwave_shutdown.register
  def my_shutdown_handler():
      slash.logger.info("SHUTDOWN!")

  ...

  # we still have to take care of actually calling our hook
  def shutdown_microwave(microwave):
      slash.hooks.microwave_shutdown() # trigger the hook
      ...

.. autofunction:: slash.hooks.add_custom_hook
.. autofunction:: slash.hooks.ensure_custom_hook
.. autofunction:: slash.hooks.remove_custom_hook


Hooks Callback Order
~~~~~~~~~~~~~~~~~~~~

In some cases it is important to order the execution of callbacks. For example, when installing a plugin that depends on a second plugin, it might be required that session_start be called in the correct order. It is possible to add a requirement to a registered callback using the `requires` decorator. When the hook is called, slash will call satisfied callbacks first, until no satisfied callbacks are left. If a callback can't be satisfied, a RequiremenetsNotMet exception will be raised

.. code-block:: python

  import slash
  
  class MicrowavePlugin(slash.plugins.PluginInterface):
    def session_start(self):
      slash.g.microwave=Microwave()
      
  class LogPlugin(slash.plugins.PluginInterface):
    @slash.hooks.requires(lambda: hasattr(slash.g,'microwave'))
    def session_start(self):
      print slash.g.microwave

