.. _exceptions:

Exceptions and Debugging
========================

.. index::
   single: exceptions
   single: debugging

Exceptions are an important part of the testing workflow. They happen all the time -- whether they indicate a test lifetime event or an actual error condition. Exceptions need to be debugged, handled, responded to, and sometimes with delicate logic of what to do when.

You can enter a debugger when exceptions occur via the ``--pdb`` flag. Slash will attempt to invoke ``pudb`` or ``ipdb`` if you have them installed, but will revert to the default ``pdb`` if they are not present.

Note that the hooks named ``exception_caught_after_debugger``, and ``exception_caught_before_debugger`` handle exception cases. It is important to plan your hook callbacks and decide which of these two hooks should call them, since a debugger might stall for a long time until a user notices it.

.. _KeyboardInterrupt:

Handling KeyboardInterrupt
--------------------------

.. index::
   single: KeyboardInterrupt
   single: interrupting

Usually when a user hits Ctrl+C this means he wants to terminate the running program as quickly as possible without corruption or undefined state. Slash treats KeyboardInterrupt a bit differently than other exceptions, and tries to quit as quickly as possible when they are encountered.

.. note:: ``KeyboardInterrupt`` also causes regular cleanups to be skipped. You can set critical cleanups to be carried out on both cases, as described in the :ref:`relevant section <cleanups>`.

Exception Handling Context
--------------------------

Exceptions can occur in many places, both in tests and in surrounding infrastructure. In many cases you want to give Slash the first oppurtunity to handle an exception before it propagates. For instance, assume you have the following code:

.. code-block:: python

    def test_function():
        func1()

    def func1():
        with some_cleanup_context():
	    func2()

    def func2():
        do_something_that_can_fail()

In the above code, if ``do_something_that_can_fail`` raises an exception, and assuming you're running slash with ``--pdb``, you will indeed be thrown into a debugger. However, the end consequence will not be what you expect, since ``some_cleanup_context`` will have already been left, meaning any cleanups it performs on exit take place *before* the debugger is entered. This is because the exception handling code Slash uses kicks in only after the exception propagates out of the test function.

In order to give Slash a chance to handle the exception closer to where it originates, Slash provices a special context, :func:`slash.exception_handling.handling_exceptions`. The purpose of this context is to give your infrastructure a chance to handle an erroneous case as close as possible to its occurrence:

.. code-block:: python

    def func1():
        with some_cleanup_context(), slash.handle_exceptions_context():
	    func2()


the :func:`handling_exceptions <slash.exception_handling.handling_exceptions>` context can be safely nested -- once an exception is handled, it is appropriately marked, so the outer contexts will skip handling it:

.. code-block:: python

    from slash.exception_handling import handling_exceptions

    def some_function():
        with handling_exceptions():
            do_something_that_might_fail()

    with handling_exceptions():
        some_function()

Exception Marks
---------------

The exception handling context relies on a convenience mechanism for marking exceptions. 



Marks with Special Meanings
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* :func:`.noswallow`
* :func:`.mark_exception_fatal`

.. note:: for more on excption swallowing, see :ref:`below <exception_swallowing>`.



.. _exception_swallowing:

Exception Swallowing
--------------------

Slash provides a convenience context for swallowing exceptions in various places, :func:`.get_exception_swallowing_context`. This is useful in case you want to write infrastructure code that should not collapse your session execution if it fails. Use cases for this feature:

1. Reporting results to external services, which might be unavailable at times
2. Automatic issue reporting to bug trackers
3. Experimental features that you want to test, but don't want to disrupt the general execution of your test suites.

Swallowed exceptions get reported to log as debug logs, and assuming the :ref:`conf.sentry.dsn` configuration path is set, also get reported to `sentry <http://getsentry.com>`_:

.. code-block:: python


   def attempt_to_upload_logs():
       with slash.get_exception_swallowing_context():
            ...



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


