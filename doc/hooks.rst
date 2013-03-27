Hooks
=====

Registering Hooks
-----------------

You can add callbacks to be called in various points of Shakedown's execution via the hook mechanism. Registering callbacks to hooks can be done via the :func:`.Callback.register` method, which can also be used as a decorator:

.. codeblock:: python

    import shakedown
    
    @shakedown.hooks.suite_start.register
    def handler():
        print("Suite has started: ", shakedown.context.suite)

Hook Errors
-----------

Since hooks are rarely related to each other, an error in a hook callback does not terminate the call chain, and is swallowed while issuing a warning. The ``hooks.swallow_exceptions`` configuration options controls this behavior. When disabled, exceptions will be propagated at the end of the call chain.

This mechanism makes use of the :ref:`exception_swallowing` mechanism of Shakedown, so you can bypass it in several ways if you want. See :ref:`the exception swallowing documentation <exception_swallowing>` for more details.

**TODO: sentry support and debuggability**

Available Hooks
---------------

The following hooks are available from the ``shakedown.hooks`` module:

.. hook_list_doc::

