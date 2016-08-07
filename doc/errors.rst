.. _errors:

Assertions, Exceptions and Errors
=================================

Assertions
----------

Assertions are the bread and butter of tests. They ensure constraints are held and that conditions are met:

.. code-block:: python

		# test_addition.py

		def test_addition(self):
		    assert 2 + 2 == 4

When assertions fail, the assertion rewriting code Slash uses will help you understand what exactly happened. This also applies for much more complex expressions:

.. code-block:: python

		...
		assert f(g(x))  == g(f(x + 1))
		...

When the above assertion fails, for instance, you can expect an elaborate output like the following::

        >        assert f(g(x)) == g(f(x + 1))
        F        AssertionError: assert 1 == 2
                 +  where 1 = <function f at 0x10b10f848>(1)
                 +    where 1 = <function g at 0x10b10f8c0>(1)
                 +  and   2 = <function g at 0x10b10f8c0>(2)
                 +    where 2 = <function f at 0x10b10f848>((1 + 1))


.. note:: The assertion rewriting code is provided by `dessert <https://github.com/vmalloc/dessert>`_, which is a direct port of the code that powers `pytest <http://pytest.org>`_. All credit goes to Holger Krekel and his fellow devs for this masterpiece.

More Assertion Utilities
~~~~~~~~~~~~~~~~~~~~~~~~

One case that is not easily covered by the assert statement is asserting Exception raises. This is easily done with :func:`slash.assert_raises`:

.. code:: python

	  with slash.assert_raises(SomeException) as caught:
	      some_func()

	  assert caught.exception.param == 'some_value'

You also have :func:`slash.assert_almost_equal` to test for near equality:

.. code:: python

	  slash.assert_almost_equal(1.001, 1, max_delta=0.1)

.. note:: :func:`slash.assert_raises` interacts with :func:`.handling_exceptions` - exceptions anticipated by ``assert_raises`` will be ignored by ``handling_exceptions``.

Errors
------

.. index::
   single: errors

Any exception which is not an assertion is considered an 'error', or in other words, an unexpected error, failing the test. Like many other testing frameworks Slash distinguishes failures from errors, the first being anticipated while the latter being unpredictable. For most cases this distinction is not really important, but exists nontheless. 

Any exceptions thrown from a test will be added to the test result as an error, thus marking the test as 'error'.

.. _KeyboardInterrupt:

Interruptions
-------------

.. index::
   single: KeyboardInterrupt
   single: interrupting

Usually when a user hits Ctrl+C this means he wants to terminate the running program as quickly as possible without corruption or undefined state. Slash treats KeyboardInterrupt a bit differently than other exceptions, and tries to quit as quickly as possible when they are encountered.

.. note:: ``KeyboardInterrupt`` also causes regular cleanups to be skipped. You can set critical cleanups to be carried out on both cases, as described in the :ref:`relevant section <cleanups>`.


Explicitly Adding Errors and Failures
-------------------------------------

.. index::
   single: add_error
   single: add_failure
   pair: errors; adding
   pair: failures; adding

Sometimes you would like to report errors and failures in mid-test without failing it immediately (letting it run to the end). This is good when you want to collect all possible failures before officially quitting, and this is more helpful for reporting.

This is possible using the :func:`slash.add_error` and :func:`slash.add_failure` methods. They can accept strings (messages) or actual objects to be kept for reporting. It is also possible to add more than one failure or error for each test.

.. code-block:: python

 class MyTest(slash.Test):
     
    def test(self):
        if not some_condition():
            slash.add_error("Some condition is not met!")

	# code keeps running here...

.. autofunction:: slash.add_error

.. autofunction:: slash.add_failure



.. _exceptions:

Handling and Debugging Exceptions
---------------------------------

.. index::
   single: exceptions
   single: debugging

Exceptions are an important part of the testing workflow. They happen all the time -- whether they indicate a test lifetime event or an actual error condition. Exceptions need to be debugged, handled, responded to, and sometimes with delicate logic of what to do when.

You can enter a debugger when exceptions occur via the ``--pdb`` flag. Slash will attempt to invoke ``pudb`` or ``ipdb`` if you have them installed, but will revert to the default ``pdb`` if they are not present.

Note that the hooks named ``exception_caught_after_debugger``, and ``exception_caught_before_debugger`` handle exception cases. It is important to plan your hook callbacks and decide which of these two hooks should call them, since a debugger might stall for a long time until a user notices it.


Exception Handling Context
~~~~~~~~~~~~~~~~~~~~~~~~~~

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

.. note:: ``handling_exceptions`` will ignore exceptions currently anticipated by :func:`.assert_raises`. This is desired since these exceptions are an expected flow and not an actual error that needs to be handled. These exceptions will be simply propagated upward without any handling or marking of any kind.

Exception Marks
~~~~~~~~~~~~~~~

The exception handling context relies on a convenience mechanism for marking exceptions. 



Marks with Special Meanings
+++++++++++++++++++++++++++

* :func:`.mark_exception_fatal`: See :ref:`below <fatal_exceptions>`.
* :func:`.noswallow`: See :ref:`below <exception_swallowing>`.


.. _fatal_exceptions:

Fatal Exceptions
~~~~~~~~~~~~~~~~

Slash supports marking special exceptions as *fatal*, causing the immediate stop of the session in which they occur. This is useful if your project has certain types of failures which are considered important enough to halt everything for investigation.

Fatal exceptions can be added in two ways. Either via marking explicitly with :func:`.mark_exception_fatal`:

.. code-block:: python
       
       ...
       raise slash.exception_handling.mark_exception_fatal(Exception('something'))

Or, when adding errors explicitly, via the ``mark_fatal`` method:

.. code-block:: python
       
       slash.add_error("some error condition detected!").mark_fatal()

.. note:: The second form, using ``add_error`` will not stop immediately since it does not raise an exception. It is your reponsibility to avoid any further actions which might tamper with your setup or your session state.


.. _exception_swallowing:

Exception Swallowing
~~~~~~~~~~~~~~~~~~~~

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


