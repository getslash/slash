.. _hooks: 

Hooks
=====

Slash leverages the `gossip library <http://gossip.readthedocs.org>`_ to implement hooks. Hooks are endpoints to which you can register callbacks to be called in specific points in a test session lifetime.

All built-in hooks are members of the ``slash`` gossip group. As a convenience, the hook objects are all kept as globals in the :mod:`slash.hooks` module.

The ``slash`` gossip group is set to be both strict (See `Gossip strict registrations <http://gossip.readthedocs.org/en/latest/advanced.html#strict-registration>`_) and has exception policy set to ``RaiseDefer`` (See `Gossip error handling <http://gossip.readthedocs.org/en/latest/error_handling.html>`_).

Registering Hooks
-----------------

Hooks can be registered through :mod:`slash.hooks`:

.. code-block:: python

    import slash
    
    @slash.hooks.session_start.register
    def handler():
        print("Session has started: ", slash.context.session)

Which is roughly equivalent to:

.. code-block:: python

  import gossip

  @gossip.register("slash.session_start")
  def handler():
        print("Session has started: ", slash.context.session)

Hook Errors
-----------

.. index::
   pair: hooks; errors in
   pair: hooks; exceptions in
   pair: debugging; hooks

By default, exceptions propagate from hooks and on to the test, but first all hooks are attempted. In some cases though you may want to debug the exception close to its raising point. Setting :ref:`conf.debug.debug_hook_handlers` to ``True`` will cause the debugger to be triggered as soon as the hook dispatcher encounteres the exception. This is done via `gossip's error handling mechanism <http://gossip.readthedocs.org/en/latest/error_handling.html>`_.

Hooks and Plugins
-----------------

Hooks are especially useful in conjunction with :ref:`plugins`. By default, plugin method names correspond to hook names on which they are automatically registered upon activation.

.. seealso:: :ref:`plugins`

Advanced Usage
--------------

You may want to further customize hook behavior in your project. Mose of these customizations are available through ``gossip``.

.. seealso:: `Advanced Usage In Gossip <http://gossip.readthedocs.org/en/latest/advanced.html>`_

.. seealso:: `Hook Dependencies <http://gossip.readthedocs.org/en/latest/hook_dependencies.html>`_


Available Hooks
---------------

The following hooks are available from the ``slash.hooks`` module:

.. hook_list_doc::

