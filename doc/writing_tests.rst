Writing Tests
=============

The easiest way to implement tests in shakedown is to write classes inheriting from :class:`shakedown.Test`.

The Basics
----------

Subclasses of :class:`shakedown.Test` are run by shakedown in a manner quite similar to the ``unittest.TestCase`` class. Classes can contain multiple methods, each will be run as a separate "case".

Shakedown only runs methods beginning with ``test`` as cases. A minimalistic test implementation, therefore, can be written as follows:

.. code-block:: python

 from shakedown import Test
 
 class SomeCoolTest(Test):
     def test(self):
         pass # <-- test logic goes here

Before and after each case, very much like ``unittest``'s ``setUp`` and ``tearDown``, :func:`shakedown.Test.before` and :func:`shakedown.Test.after` are run respectively. This is very useful when including multiple test cases in a single class:

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

 import shakedown

 def microwave_power_on_sequence(microwave):
     microwave.plug_to_outlet()
     shakedown.add_cleanup(microwave.plug_out_of_outlet)
     microwave.press_power()
     shakedown.add_cleanup(microwave.wait_until_off)
     shakedown.add_cleanup(microwave.press_power)
     microwave.wait_until_on()

 class MicrowaveTest(shakedown.Test):
     def begin(self):
         # ...
         microwave_power_on_sequence(self.microwave)
     def test_microwave_is_working(self):
         shakedown.should.be_true(self.microwave.is_working())

.. autofunction:: shakedown.add_cleanup

Skips
-----

In some case you want to skip certain methods. This is done by raising the :class:`.SkipTest` exception, or by simply calling :func:`skip_test` function:

.. code-block:: python

 class MicrowaveTest(shakedown.Test):
     # ...
     def test_has_supercool_feature(self):
         if self.microwave.model() == "Microtech Shitbox":
             shakedown.skip_test("Microwave model too old")

Shakedown also provides :func:`skipped`, which is a decorator to skip specific methods or entire classes:

.. code-block:: python

 class MicrowaveTest(shakedown.Test):
     @shakedown.skipped("reason")
     def test_1(self):
         # ...
     @shakedown.skipped # no reason
     def test_2(self):
         # ...

 @shakedown.skipped("reason")
 class EntirelySkippedTest(shakedown.Test):
     # ...


.. autoclass:: shakedown.exceptions.SkipTest

.. autofunction:: shakedown.skip_test


Advanced Features
-----------------

Abstract Base Tests
~~~~~~~~~~~~~~~~~~~

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

If you try running the above code via Shakedown, it will fail. This is because Shakedown tries to run all cases in ``FileTestBase``, which cannot run due to the lack of a ``before()`` method.

This is solved with the :func:`shakedown.abstract_test_class` decorator:

.. code-block:: python
  
    @shakedown.abstract_test_class
    class FileTestBase(Test):
        def test_has_write_method(self):
            assert_true(hasattr(self.file, "write"))
        def test_has_read_method(self):
            assert_true(hasattr(self.file, "read"))

.. autofunction:: shakedown.abstract_test_class

Test Parameters
~~~~~~~~~~~~~~~

Shakedown's :class:`.Test` supports adding parameters to your tests via the ``shakedown.parameters`` module.

Use the :func:`shakedown.parameters.iterate` decorator to multiply a test function for different parameter values:

.. code-block:: python

    class SomeTest(Test):
        @shakedown.parameters.iterate(x=[1, 2, 3])
	def test(self, x):
            # use x here

The above example will yield 3 test cases, one for each value of ``x``. It is also useful to provide parameters to the ``before`` and ``after`` methods, thus multiplying each case by several possible setups:

.. code-block:: python

    class SomeTest(Test):
        @shakedown.parameters.iterate(x=[1, 2, 3])
	def before(self, x):
            # ...

        @shakedown.parameters.iterate(y=[4, 5, 6])
	def test(self, y):
            # ...

        @shakedown.parameters.iterate(z=[7, 8, 9])
	def after(self, z):
            # ...

The above will yield 9 different runnable tests, one for each cartesian product of the ``before``, ``test`` and ``after`` possible parameter values.
