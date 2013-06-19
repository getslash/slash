Writing Tests
=============

The easiest way to implement tests in slash is to write classes inheriting from :class:`slash.Test`.

The Basics
----------

Subclasses of :class:`slash.Test` are run by slash in a manner quite similar to the ``unittest.TestCase`` class. Classes can contain multiple methods, each will be run as a separate "case".

Slash only runs methods beginning with ``test`` as cases. A minimalistic test implementation, therefore, can be written as follows:

.. code-block:: python

 from slash import Test
 
 class SomeCoolTest(Test):
     def test(self):
         pass # <-- test logic goes here

Before and after each case, very much like ``unittest``'s ``setUp`` and ``tearDown``, :func:`slash.Test.before` and :func:`slash.Test.after` are run respectively. This is very useful when including multiple test cases in a single class:

.. code-block:: python

 class MicrowaveTest(Test):
     def before(self):
         self.microwave = Microwave(...)

     def test_has_buttons(self):
         # ...
     def test_can_power_on(self):
         # ...
     # more tests...

     def after(self):
         self.microwave.turn_off()

Note that in such cases, each case will be invoked on a fresh copy of ``MicrowaveTest`` (i.e. it will be reconstructed for every test case method).

.. seealso:: :ref:`logging`

Errors and Failures
-------------------

Almost any exception encountered during test execution is considered an *error*. 

A special case is reserved for exceptions raised from failed assertions (See :ref:`assertion functions <assertions>` for more information). These assertions are considered *failures*.

The differentiation between errors and failures is important -- failures are specific checks that have failed, while errors are anything else. In failure cases, for instance, it is likely to encounter a meaningful description of what exactly failed (e.g. ``some_predicate()`` unexpectedly returned False). Errors are far less predictable, and can mean anything from an ``assert`` statement hidden inside your code to an ``ImportError`` or even ``SyntaxError`` when importing a module.

The :class:`.exceptions.TestFailed` exception (or any class derived from it) is used to indicate a failure. It is raised from all :ref:`assertion functions<assertions>`.

.. note:: Unlike in ``unittest``, ``AssertionError`` **DOES NOT** mean a failure, but rather an error. This is mainly because you wouldn't want internal assertions in your code and/or libraries that you use to be considered failures.

Cleanups
--------

Cleanups functions can be added from anywhere in your code (not just the runnable test class), through the :func:`.add_cleanup` function. Once added to the cleanup list, cleanup callbacks will be executed in reverse order when tests are finished. This enables you to call ``add_cleanup`` from utility libraries and toolkits:

.. code-block:: python

 import slash

 def microwave_power_on_sequence(microwave):
     microwave.plug_to_outlet()
     slash.add_cleanup(microwave.plug_out_of_outlet)
     microwave.press_power()
     slash.add_cleanup(microwave.wait_until_off)
     slash.add_cleanup(microwave.press_power)
     microwave.wait_until_on()

 class MicrowaveTest(slash.Test):
     def begin(self):
         # ...
         microwave_power_on_sequence(self.microwave)
     def test_microwave_is_working(self):
         slash.should.be_true(self.microwave.is_working())

.. autofunction:: slash.add_cleanup

Skips
-----

In some case you want to skip certain methods. This is done by raising the :class:`.SkipTest` exception, or by simply calling :func:`skip_test` function:

.. code-block:: python

 class MicrowaveTest(slash.Test):
     # ...
     def test_has_supercool_feature(self):
         if self.microwave.model() == "Microtech Shitbox":
             slash.skip_test("Microwave model too old")

Slash also provides :func:`skipped`, which is a decorator to skip specific methods or entire classes:

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


.. autoclass:: slash.exceptions.SkipTest

.. autofunction:: slash.skip_test

Global State
------------

Slash uses global (thread-local) objects for various purposes. This is particularly useful for accessing them from utility libraries and external packages.

.. _sessions:

Session
+++++++

The :class:`.Session` represents the current test execution session. It has a unique id, used to designate the session in various contexts. Tests must run under an active session, as the test results and other important pieces of data are kept on it.

The currently active session is accessible through ``slash.session``:

.. code-block:: python

  from slash import session

  print("The current session id is", session.id)

.. autoclass:: slash.session.Session
  :members:

.. _global_storage:

The Global Storage
++++++++++++++++++

In many cases objects need to be passed between tests and utility libraries. These libraries don't want to be aware of the interface of the currently running test, but would rather a single place to hold the shared state. ``slash.g`` is such a placeholder. It can be assigned with various objects and values that comprise the global state of the current run:

.. code-block:: python

  from slash import g
  
  # ...
  
  g.obj = some_object

This is particularly useful for customization purposes, :ref:`as described in the relevant section <building_solution>`.


Advanced Features
-----------------

Test Contexts
+++++++++++++

Test contexts allow you to specify a set of contexts enveloping your tests. These can control what happens before and after each test case.

This feature is useful when you don't want to complicate your tests by inheriting from several base classes acting as setup/teardown bases, but still would like the surrounding environment to be composable.

To implement a test context you create a class deriving from :class:`slash.test_context.TestContext`:

.. code-block:: python

 from slash import TestContext, g
 import subprocess

 class ProcessRunningContext(TestContext):
     """Ensure that the program we're testing is still running before each test, and runs it if needed"""
     def before_case(self):
         process = getattr(g, "process", None)
         if process is None or process.poll() is not None:
             # run/rerun our process
	     g.process = subprocess.Popen(....)


Now we wrap an ordinary test with the context using the :func:`slash.test_context.with_context` helper:

.. code-block:: python

  from slash import with_context, Test

  @with_context(ProcessRunningContext)
  class ProcessTest(Test):
      def test(self):
          ... # do something with slash.g.process


.. autoclass:: slash.test_context.TestContext

When a test context is first entered, its :func:`slash.test_context.TestContext.before` method is called. After that, each time a case is started and finished, the :func:`slash.test_context.TestContext.before_case` and :func:`slash.test_context.TestContext.after_case` are called respectively.

Test contexts are carried from case to case and from class to class. Whenever a context is not needed anymore in a new case or class about to be run, it is terminated (calling its :func:`slash.test_context.TestContext.after` method).

Abstract Base Tests
+++++++++++++++++++

Sometimes you want tests that won't be executed on their own, but rather function as bases to derived tests:

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

.. autofunction:: slash.abstract_test_class

Test Parameters
+++++++++++++++

Slash's :class:`.Test` supports adding parameters to your tests via the ``slash.parameters`` module.

Use the :func:`slash.parameters.iterate` decorator to multiply a test function for different parameter values:

.. code-block:: python

    class SomeTest(Test):
        @slash.parameters.iterate(x=[1, 2, 3])
	def test(self, x):
            # use x here

The above example will yield 3 test cases, one for each value of ``x``. It is also useful to provide parameters to the ``before`` and ``after`` methods, thus multiplying each case by several possible setups:

.. code-block:: python

    class SomeTest(Test):
        @slash.parameters.iterate(x=[1, 2, 3])
	def before(self, x):
            # ...

        @slash.parameters.iterate(y=[4, 5, 6])
	def test(self, y):
            # ...

        @slash.parameters.iterate(z=[7, 8, 9])
	def after(self, z):
            # ...

The above will yield 9 different runnable tests, one for each cartesian product of the ``before``, ``test`` and ``after`` possible parameter values.
