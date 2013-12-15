Exceptions and Debugging
========================

Exceptions are an important part of the testing workflow. They happen all the time -- whether they indicate a test lifetime event or an actual error condition. Exceptions need to be debugged, handled, responded to, and sometimes with delicate logic of what to do when.

You can enter a debugger when exceptions occur via the ``--pdb`` flag. Slash will attempt to invoke ``pudb`` or ``ipdb`` if you have them installed, but will revert to the default ``pdb`` if they are not present.

Note that the hooks named ``exception_caught_after_debugger``, and ``exception_caught_before_debugger`` handle exception cases. It is important to plan your hook callbacks and decide which of these two hooks should call them, since a debugger might stall for a long time until a user notices it.

.. _KeyboardInterrupt:

Handling KeyboardInterrupt
--------------------------

Usually when a user hits Ctrl+C this means he wants to terminate the running program as quickly as possible without corruption or undefined state. Slash treats KeyboardInterrupt a bit differently than other exceptions, and tries to quit as quickly as possible when they are encountered.

.. note:: ``KeyboardInterrupt`` also causes regular cleanups to be skipped. You can set critical cleanups to be carried out on both cases, as described in the :ref:`relevant section <cleanup>`.

Exception Handling Context
--------------------------

Slash contains a special context, :func:`slash.handling_exceptions`. The purpose of this context is to give your infrastructure a chance to handle an erroneous case as close as possible to its occurrence. 

This context can be safely nested -- once an exception is handled, it is appropriately marked, so the outer contexts will skip handling it:

.. code-block:: python

    from slash import handling_exceptions

    def some_function():
        with handling_exceptions():
            do_something_that_might_fail()

    with handling_exceptions():
        some_function()

.. autofunction:: slash.exception_handling.handling_exceptions

Exception Marks
---------------

The exception handling context relies on a convenience mechanism for marking exceptions. 

.. autofunction:: slash.exception_handling.is_exception_marked
.. autofunction:: slash.exception_handling.mark_exception
.. autofunction:: slash.exception_handling.get_exception_mark


Marks with Special Meanings
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: slash.exception_handling.noswallow

.. note:: for more on excption swallowing, see :ref:`below <exception_swallowing>`.

.. autofunction:: slash.exception_handling.mark_exception_fatal


.. _exception_swallowing:

Exception Swallowing
--------------------

Slash provides a convenience context for swallowing exceptions in various places. This is useful in case you want to write fail-safe code. This is done with :func:`.get_exception_swallowing_context`.

Swallowed exceptions get reported to log as debug logs, and assuming the :ref:`conf.sentry.dsn` configuration path is set, also get reported to `sentry <http://getsentry.com>`_.

You can force certain exceptions through by using the :func:`.noswallow` or ``disable_exception_swallowing`` functions:

.. code-block:: python

   from slash.exception_handling import (
       noswallow,
       disable_exception_swallowing,
       )

   def func1():
      raise noswallow(Exception("CRITICAL!"))

   def func2():
      e = Exception("CRITICAL!")
      disable_exception_swallowing(e)
      raise e

   @disable_exception_swallowing
   def func3():
      raise Exception("CRITICAL!")

.. autofunction:: slash.exception_handling.get_exception_swallowing_context

