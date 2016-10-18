Whirlwind Tour of Slash
=======================

.. _tour:

Writing Tests
-------------

Slash loads and runs tests from Python files. To get started, let's create an example test file and name it ``test_addition.py``:

.. code-block:: python

		# test_addition.py

		import slash

		def test_addition():
		    pass

As you can see in the above example, Slash can load tests written as functions. Simlarly to ``unittest`` and ``py.test``, only functions starting with the prefix ``test_`` are assumed to be runnable tests.

Running Tests
-------------

Once we have our file written, we can run it using ``slash run``::

  $ slash run test_addition.py

There's a lot to cover regarding ``slash run``, and we will get to it :ref:`soon enough <slash_run>`. For now all we have to know is that it finds, loads and runs the tests in the files or directories we provide, and reports the result.

A single run of ``slash run`` is called a *session*. A session contains tests that were run in its duration.

Debugging
~~~~~~~~~

You can debug failing tests using the ``--pdb`` flag, which automatically runs the best available debugger on exceptions. 

.. seealso:: :ref:`exceptions`


Assertions and Errors
---------------------

Tests don't do much without making sure things are like they expect. Slash borrows the awesome technology behind ``py.test``, allowing us to just write assert statements where we want to test conditions of all sorts:

.. code-block:: python

		# test_addition.py

		def test_addition():
		    assert 2 + 2 == 4

Slash also analyzes assertions using assertion rewriting borrowed from the `pytest project <http://pytest.org>`_, so you can get more details as for what exactly failed.

.. seealso:: errors

Test Parameters
---------------

Slash tests can be easily parametrized, iterating parameter values and creating separate cases for each value:

.. code-block:: python

   @slash.parametrize('x', [1, 2, 3])
   def test_something(x):
       # use x here

For boolean values, a shortcut exists for toggling between ``True`` and ``False``:

.. code-block:: python
       
   @slash.parameters.toggle('with_power_operator')
   def test_power_of_two(with_power_operator):
       num = 2
       if with_power_operator:
           result = num ** 2
       else:
           result = num * num
       assert result == 4

.. seealso:: :ref:`parameters`

Logging
-------

Testing complete products usually means you may not have a second chance to reproduce an issue. This is why Slash puts a strong emphasis on logging, managing log files and directories, and fine tuning your logging setup.

Slash uses `Logbook <http://logbook.pocoo.org>`_ for logging. It has many advantages over Python's own ``logging`` package, and is much more flexible.

Slash exposes a global logger intended for tests, which is recommended for use in simple logging tasks:

.. code-block:: python

 import slash

 def test_1():
     slash.logger.debug("Hello!")


Console Log
~~~~~~~~~~~

.. index:: 
   pair: console; log
   pair: log; console
   

By default logs above **WARNING** get emitted to the console when ``slash run`` is executed. You can use **-v**/**-q** to increase/decrease console verbosity accordingly.

Saving Logs to Files
~~~~~~~~~~~~~~~~~~~~

By default logs are not saved anywhere. This is easily changed with the *-l* flag to ``slash run``. Point this flag to a directory, and Slash will organize logs inside, in subdirectories according to the session and test run (e.g. ``/path/to/logdir/<session id>/<test id>/debug.log``). 

.. seealso:: :ref:`logging`


.. _cleanups:

Cleanups
--------

Slash provides a facility for cleanups. These get called whenever a test finishes, successfully or not. Adding cleanups is done with :func:`slash.add_cleanup`:

.. code-block:: python

	    def test_product_power_on_sequence():
	        product = ...
		product.plug_to_outlet()
		slash.add_cleanup(product.plug_out_of_outlet)
		product.press_power()
		slash.add_cleanup(product.wait_until_off)
		slash.add_cleanup(product.press_power)
		slash.add_cleanup(product.pack_for_shipping, success_only=True)
		product.wait_until_on()

.. note:: When a test is interrupted, most likely due to a ``KeyboardInterrupt``, cleanups are not called unless added with the ``critical`` keyword argument. This is in order to save time during interruption handling. See :ref:`interruptions <KeyboardInterrupt>`.

.. note:: A cleanup added with ``success_only=True`` will be called only if the test ends successfully

Cleanups also receive an optional ``scope`` parameter, which can be either ``'session'``, ``'module'`` or ``'test'`` (the default). The ``scope`` parameter controls *when* the cleanup should take place. *Session* cleanups happen at the end of the test session, *module* cleanups happen before Slash switches between test files during execution and *test* cleanups happen at the end of the test which added the cleanup callback.

Skips
-----

.. index::
   pair: tests; skipping
   pair: skipping; tests

In some case you want to skip certain methods. This is done by raising the :class:`.SkipTest` exception, or by simply calling :func:`slash.skip_test` function:

.. code-block:: python

   def test_microwave_has_supercool_feature():
       if microwave.model() == "Microtech Shitbox":
           slash.skip_test("Microwave model too old")

Slash also provides :func:`slash.skipped`, which is a decorator to skip specific tests:

.. code-block:: python

     @slash.skipped("reason")
     def test_1():
         # ...

     @slash.skipped # no reason
     def test_2():
         # ...

In some cases you may want to register a custom exception to be recognized as a skip. You can do this by registering your exception type first with :func:`slash.register_skip_exception`.


Requirements
------------
In many cases you want to depend in our test on a certain precondition in order to run. Requirements provide an explicit way of stating those requirements. Use :func:`slash.requires` to specify requirements:

.. code-block:: python


  def is_some_condition_met():
      return True
		
  @slash.requires(is_some_condition_met)
  def test_something():
      ...

Requirements are stronger than skips, since they can be reported separately and imply a basic precondition that is not met in the current testing environment. 

``slash.requires`` can receive either:

1. A boolean value (useful for computing on import-time)
2. A function returning a boolean value, to be called when loading tests
3. A function returning a tuple of (boolean, message) - the message being the description of the unmet requirements when ``False`` is returned

When a requirement fails, the test is skipped without even being started, and appears in the eventual console summary along with the unmet requirements. If you want to control the message shown if the requirement is not met, you can pass the ``message`` parameter:

.. code-block:: python
       
  @slash.requires(is_some_condition_met, message='My condition is not met!')
  def test_something():
      ...


.. note::
   Requirements are evaluated during the load phase of the tests, so they are usually checked before any test started running. This means that if you're relying on a transient state that can be altered by other tests, you have to use skips instead. Requirements are useful for checking environmental constraints that are unlikely to change as a result of the session being run.

Warnings
--------

In many cases test executions succeed, but warnings are emitted. These warnings can mean a lot of things, and in some cases even invalidate the success of the test completely.

Slash collects warnings emitted throughout the session in the form of either *warning logs* or the *native warnings mechanism*. The warnings are recorded in the ``session.warnings`` (instance of :class:`.warnings.SessionWarnings`) component, and cause the ``warning_added`` hook to be fired.


Storing Additional Test Details
-------------------------------

It is possible for a test to store some objects that may help investigation in cause of failure.

This is possible using the :func:`slash.set_test_detail` method. This method accepts a hashable key object and a printable object. In case the test fails, the stored objects will be printed in the test summary:

.. code-block:: python

    def test_one():
        slash.set_test_detail('log', '/var/log/foo.log')
        slash.set_error("Some condition is not met!")

    def test_two():
        # Every test has its own unique storage, so it's possible to use the same key in multiple tests
        slash.set_test_detail('log', '/var/log/bar.log')

In this case we probably won't see the details of test_two, as it should finish successfully.

.. autofunction:: slash.set_test_detail


.. _global_state:

Global State
------------

Slash maintains a set of globals for convenience. The most useful one is ``slash.g``, which is an attribute holder that can be used to hold environment objects set up by plugins or hooks for use in tests.


Misc. Utilities
---------------

Repeating Tests
~~~~~~~~~~~~~~~

Use the :func:`slash.repeat` decorator to make a test repeat several times:

.. code-block:: python
       
       @slash.repeat(5)
       def test_probabilistic():
           assert still_works()

.. note:: You can also use the ``--repeat-each=X`` argument to `slash run`, causing it to repeat each test being loaded a specified amount of times, or ``--repeat-all=X`` to repeat the entire suite several times
