.. _parameters:

Test Parametrization
====================

Using slash.parametrize
-----------------------

Use the :func:`slash.parametrize` decorator to multiply a test function for different parameter values:

.. code-block:: python
       
       @slash.parametrize('x', [1, 2, 3])
       def test_something(x):
           pass

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


More Parametrization Shortcuts
------------------------------

In addition to :func:`slash.parametrize`, Slash also supports :func:`slash.parameters.toggle <slash.core.fixtures.parameters.toggle>` as a shortcut for toggling a boolean flag in two separate cases:

.. code-block:: python

		@slash.parameters.toggle('with_safety_switch')
		def test_operation(with_safety_switch):
		    ...

Another useful shortcut is :func:`slash.parameters.iterate <slash.core.fixtures.parameters.iterate>`, which is an alternative way to specify parametrizations:

.. code-block:: python
       
		@slash.parameters.iterate(x=[1, 2, 3], y=[4, 5, 6])
		def test_something(x, y):
		    ...



Specifying Multiple Arguments at Once
-------------------------------------

You can specify dependent parameters in a way that forces them to receive related values, instead of a simple cartesian product:

.. code-block:: python
       
       @slash.parametrize(('fruit', 'color'), [('apple', 'red'), ('apple', 'green'), ('banana', 'yellow')])
       def test_fruits(fruit, color):
           ... # <-- this never gets a yellow apple

Excluding Parameter Values
--------------------------

.. index::
   single: exclude
   single: slash.exclude


You can easily skip specific values from parametrizations in tests through ``slash.exclude``:

.. code-block:: python
       
       import slash

       SUPPORTED_SIZES = [10, 15, 20, 25]

       @slash.parametrize('size', SUPPORTED_SIZES)
       @slash.exclude('size', [10, 20])
       def test_size(size): # <-- will be skipped for sizes 10 and 20
           ...

This also works for parameters of fixtures (for more information about fixtures see :ref:`the fixtures chapter <fixtures>`)

.. code-block:: python
       
       import slash

       SUPPORTED_SIZES = [10, 15, 20, 25]

       @slash.exclude('car.size', [10, 20])
       def test_car(car):
           ...

       @slash.parametrize('size', SUPPORTED_SIZES)
       @slash.fixture
       def car(size): # <-- will be skipped for sizes 10 and 20
           ...


