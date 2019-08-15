.. _warnings:

Warnings
========

In many cases test executions succeed, but warnings are emitted. These warnings can mean a lot of things, and in some cases even invalidate the success of the test completely.

Warning Capture
---------------

Slash collects warnings emitted throughout the session in the form of either *warning logs* or the *native warnings mechanism*. The warnings are recorded in the ``session.warnings`` (instance of :class:`.warnings.SessionWarnings`) component, and cause the ``warning_added`` hook to be fired.


Filtering Warnings
------------------

By default all native warnings are captured. In cases where you want to silence specific warnings, you can use the :func:`slash.ignore_warnings` function to handle them.

For example, you may want to include code in your project's ``.slashrc`` as follows:

.. code-block:: python

                @slash.hooks.configure.register
                def configure_warnings():
                    slash.ignore_warnings(category=DeprecationWarning, filename='/some/bad/file.py')


.. note:: Filter arguments to ignore_warnings are treated as though they are ``and`` ed together. This means that a filter for a specific filename and a specific category would only ignore warnings coming from the specified file *and* having the specified category.

For ignoring warnings in specific code-block, one can use the `slash.ignored_warnings` context:
.. code-block:: python

                with slash.ignore_warnings(category=DeprecationWarning, filename='/some/bad/file.py'):
                    ...
