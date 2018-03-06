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
