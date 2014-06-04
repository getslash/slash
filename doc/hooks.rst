.. _hooks: 

Hooks
=====

Slash leverages the `gossip library <http://gossip.readthedocs.org>`_ to implement hooks. Hooks are endpoints to which you can register callbacks to be called in specific points in a test session lifetime.

All built-in hooks are members of the ``slash`` gossip group. As a convenience, the hook objects are all kept as globals in the :mod:`slash.hooks` module.

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

Errors encountered in hooks are subject to how gossip handles exceptions. See `the relevant documentation <http://gossip.readthedocs.org/en/latest/error_handling.html>`_ for more details.

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

