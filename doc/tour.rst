Whirlwind Tour of Slash
=======================

.. _tour:

Writing Tests
-------------

Slash loads and runs tests from Python files. To get started, let's create an examplet test file and name it ``test_addition.py``:

.. code-block:: python

		# test_addition.py

		import slash

		class AdditionTest(slash.Test):
		    
		    def test_addition(self):
		        pass

As you can see in the above example, Slash can load tests written as classes. These classes must derive from the :class:`slash.Test` class. Also, simlarly to ``unittest``, each method starting with the prefix ``test`` is assumed to be a runnable test.

.. note:: Slash supports a more modern form of tests -- functions. These are plain functions beginning with the prefix ``test_``. However, this feature is mostly useful when combined with fixtures. See :ref:`the relevant section <fixtures>` for more details.		     

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

		def test_addition(self):
		    assert 2 + 2 == 4

Slash also analyzes assertions using assertion rewriting borrowed from the `pytest project <http://pytest.org>`_, so you can get more details as for what exactly failed.

.. seealso:: errors


Test Setups and Teardowns
-------------------------

.. index:: 
   single: before
   pair: before; method
   single: after
   pair: after; method

When writing tests as classes, you can control the setup and teardown code for each case using the ``before`` and ``after`` methods, which happen before and after each test case method respectively:

.. code-block:: python

		# test_addition.py

		import slash

		class AdditionTest(slash.Test):

		    def before(self):
		        self.sum = 2 + 2

		    def after(self):
		        # ...
		    
		    def test_addition(self):
		        assert self.sum == 4

.. note:: ``after`` is not called if ``before`` doesn't complete successfully. For more robust cleanups, see :ref:`cleanups`.

Logging
-------

Slash is built with product tests. This means you may not have a second chance to reproduce an issue, and more emphasis is put on logging.

Slash uses `Logbook <http://logbook.pocoo.org>`_ for logging. It has many advantages over Python's own ``logging`` package, and is much more flexible.

Slash exposes a global logger intended for tests, which is recommended for use in simple logging tasks:

.. code-block:: python

 import slash

 class SomeTest(slash.Test):

     def test_1(self):
         slash.logger.debug("Hello!")


Console Log
~~~~~~~~~~~

.. index:: 
   pair: console; log
   pair: log; console
   

By default logs above **WARNING** get emitted to the console when ``slash run`` is executed. You can use **-v**/**-q** to increase/decrease console verbosity accordingly.

Saving Logs to Files
~~~~~~~~~~~~~~~~~~~~

By default logs are not saved anywhere. This is easily changed with the *-l* flag to ``slash run``. Point this flag to a directory, and Slash will organize logs inside, in subdirectories according to the session and test run (e.g. ``/path/to/logdir/<session id>/<test id>/debug.log``). See :ref:`logging` for more details.


.. _cleanups:

Cleanups
--------

Slash provides a facility for cleanups. These get called whenever a test finishes, successfully or not. Adding cleanups is done with :func:`slash.add_cleanup`:

.. code-block:: python

		class SampleTest(slash.Test):
		    ...
		    def test_product_power_on_sequence(self):
		        self.product.plug_to_outlet()
			slash.add_cleanup(self.product.plug_out_of_outlet)
			self.product.press_power()
			slash.add_cleanup(self.product.wait_until_off)
			slash.add_cleanup(self.product.press_power)
			slash.add_cleanup(self.product.pack_for_shipping, success_only=True)
			self.product.wait_until_on()

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

 class MicrowaveTest(slash.Test):
     # ...
     def test_has_supercool_feature(self):
         if self.microwave.model() == "Microtech Shitbox":
             slash.skip_test("Microwave model too old")

Slash also provides :func:`slash.skipped`, which is a decorator to skip specific methods or entire classes:

.. code-block:: python

 class MicrowaveTest(slash.Test):
     @slash.skipped("reason")
     def test_1(self):
         # ...
     @slash.skipped # no reason
     def test_2(self):
         # ...

 @slash.skipped("reason")
 class EntirelySkippedTest(slash.Test):
     # ...

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

When a requirement fails, the test is skipped without even being started, and appears in the eventual console summary along with the unmet requirements. If you want to control the message shown if the requirement is not met, you can pass the ``message`` parameter:

.. code-block:: python
       
  @slash.requires(is_some_condition_met, message='My condition is not met!')
  def test_something():
      ...

When writing tests as classes, you can also decorate the class itself with requirements, and even add requirements only to specific methods:

.. code-block:: python
       
  @slash.requires(running_microwave)
  class MicrowaveTest(slash.Test):

       def test_is_running(self):
           assert microwave.is_running()

       @slash.requires(is_cold_food_available)
       def test_heating(self):
           food = get_cold_food()
	   microwave.heat(food)
	   assert food.is_hot()



Warnings
--------

In many cases test executions succeed, but warnings are emitted. These warnings can mean a lot of things, and in some cases even invalidate the success of the test completely.

Slash collects warnings emitted through loggers in the ``session.warnings`` (instance of :class:`.warnings.SessionWarnings`)


Storing Additional Test Details
-------------------------------

It is possible for a test to store some objects that may help investigation in cause of failure.

This is possible using the :func:`slash.set_test_detail` method. This method accepts a hashable key object and a printable object. In case the test fails, the stored objects will be printed in the test summary:

.. code-block:: python

 class MyTest(slash.Test):

    def test_one(self):
        slash.set_test_detail('log', '/var/log/foo.log')
        slash.set_error("Some condition is not met!")

    def test_two(self):
        # Every test has its own unique storage, so it's possible to use the same key in multiple tests
        slash.set_test_detail('log', '/var/log/bar.log')

In this case we probably won't see the details of test_two, as it should finish successfully.

.. autofunction:: slash.set_test_detail


.. _global_state:

Global State
------------

Slash maintains a set of globals for convenience. The most useful one is ``slash.g``, which is an attribute holder that can be used to hold environment objects set up by plugins or hooks for use in tests.

Test Parameters
---------------

Slash tests can be easily parametrized, iterating parameter values and creating separate cases for each value. This is true for both tests implemented as classes and for tests implemented as functions.


.. code-block:: python

   @slash.parametrize('x', [1, 2, 3])
   def test_something(x):
       # use x here

.. seealso:: :ref:`parameters`


Abstract Base Tests
-------------------

When writing test classes, sometimes you want tests that won't be executed on their own, but rather function as bases to derived tests:

.. code-block:: python

    class FileTestBase(Test):
        def test_has_write_method(self):
            assert_true(hasattr(self.file, "write"))
        def test_has_read_method(self):
            assert_true(hasattr(self.file, "read"))
    
    class RegularFileTest(FileTestBase):
        def before(self):
            super(RegularFileTest, self).before()
            self.file = open("somefile", "wb")
    
    class SocketFileTest(FileTestBase):
        def before(self):
            super(SocketFileTest, self).before()
            self.file = connect_to_some_server().makefile()

If you try running the above code via Slash, it will fail. This is because Slash tries to run all cases in ``FileTestBase``, which cannot run due to the lack of a ``before()`` method.

This is solved with the :func:`slash.abstract_test_class` decorator:

.. code-block:: python
  
    @slash.abstract_test_class
    class FileTestBase(Test):
        def test_has_write_method(self):
            assert_true(hasattr(self.file, "write"))
        def test_has_read_method(self):
            assert_true(hasattr(self.file, "read"))

Misc. Utilities
---------------

Repeating Tests
~~~~~~~~~~~~~~~

Use the :func:`slash.repeat` decorator to make a test repeat several times:

.. code-block:: python
       
       @slash.repeat(5)
       def test_probabilistic():
           assert still_works()

.. note:: You can also use the `--repeat-each=X` argument to `slash run`, causing it to repeat each test being loaded a specified amount of times
