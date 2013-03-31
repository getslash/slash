The ``shakedown.Test`` Class
============================

The ``shakedown.Test`` class is a fusion between :class:`.RunnableTest` and :class:`.RunnableTestFactory`, where the generated tests are customized constructions of the test itself.

The Basics
----------

By default, derivatives of the ``shakedown.Test`` class will run all methods beginning with ``test``, each as a separate runnable test. This is similar to the ``unittest.TestCase`` behavior. The ``before`` and ``after`` methods, if exist, will be called before and after each runnable test as a setup/teardown fixture (this is also similar to ``setUp``, ``tearDown`` from ``unittest``). Very much like ``tearDown``, ``after`` will only be called if ``before`` finished successfully, and it will be called even in the face of failures and errors.

Abstract Base Tests
-------------------

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
---------------

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
