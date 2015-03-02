Testing with Slash
==================

.. _writing_tests:

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


Assertions
----------

Tests don't do much without making sure things are like they expect. Slash borrows the awesome technology behind ``py.test``, allowing us to just write assert statements where we want to test conditions of all sorts:

.. code-block:: python

		# test_addition.py

		import slash

		class AdditionTest(slash.Test):
		    
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

Logging To Files
----------------

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


Explicitly Adding Errors
------------------------

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

.. _parameters:

Slash tests can be easily parametrized, iterating parameter values and creating separate cases for each value. This is true for both tests implemented as classes and for tests implemented as functions.

Use the :func:`slash.parametrize` decorator to multiply a test function for different parameter values:

.. code-block:: python

   @slash.parametrize('x', [1, 2, 3])
   def test_something(x):
       # use x here

The above example will yield 3 test cases, one for each value of ``x``. Slash also supports parametrizing the ``before`` and ``after`` methods of test classes, thus multiplying each case by several possible setups:

.. code-block:: python

    class SomeTest(Test):
        @slash.parametrize('x', [1, 2, 3])
	def before(self, x):
            # ...

        @slash.parametrize('y', [4, 5, 6])
	def test(self, y):
            # ...

        @slash.parametrize('z', [7, 8, 9])
	def after(self, z):
            # ...

The above will yield 27 different runnable tests, one for each cartesian product of the ``before``, ``test`` and ``after`` possible parameter values.

This also works across inheritence. Each base class can parametrize its `before` or `after` methods, multiplying the number of variations actually run accordingly. Calls to `super` are handled automatically in this case:

.. code-block:: python

    class BaseTest(Test):

        @slash.parametrize('base_parameter', [1, 2, 3])
        def before(self, base_parameter):
            # ....

    class DerivedTest(BaseTest):
        
        @slash.parametrize('derived_parameter', [4, 5, 6])
        def before(self, derived_parameter):
            super(DerivedTest, self).before() # note that base parameters aren't specified here
            # .....

Slash also supports :func:`slash.parameters.toggle <slash.core.fixtures.parameters.toggle>` as a shortcut for toggling a boolean flag in two separate cases:

.. code-block:: python

		@slash.parameters.toggle('with_safety_switch')
		def test_operation(with_safety_switch):
		    ...

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
