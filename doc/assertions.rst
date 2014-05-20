.. _assertions:

Assertions
==========

Tests rely on *assertions* to test various invariants or conditions. If you're familiar with Python's ``unittest``, such assertions are encouraged in the form of methods (e.g. ``self.assertEquals(x, y)``). The purpose of this is to allow more information about assertion failures other than the non-informative ``AssertionError:`` string.

Relying on methods has many downsides, especially that it is cumbersome, requires memorizing method names and hinders the use of utility libraries (this is because they require access to **self**).

Slash provides several ways to work around this.

Assertion Rewriting
~~~~~~~~~~~~~~~~~~~

First, it leverages AST rewriting of assertions, so that this code:

.. code-block:: python

		def f(value):
		    return value

		def g(value):
		    return value

		x = 1

		assert f(g(x)) == g(f(x+1))

When run inside a test, yields this textual exception::

        >        assert f(g(x)) == g(f(x + 1))
        F        AssertionError: assert 1 == 2
                 +  where 1 = <function f at 0x10b10f848>(1)
                 +    where 1 = <function g at 0x10b10f8c0>(1)
                 +  and   2 = <function g at 0x10b10f8c0>(2)
                 +    where 2 = <function f at 0x10b10f848>((1 + 1))

This obsoletes the need for the old methods.

.. note:: The assertion rewriting code is provided by `dessert <https://github.com/vmalloc/dessert>`_, which is a direct port of the code that powers `pytest <http://pytest.org>`_. All credit goes to Holger Krekel and his fellow devs for this masterpiece.

Assertion Helpers
~~~~~~~~~~~~~~~~~

In some cases you might prefer using explicit function helpers to perform assertions. Slash has those too.

To quickly import all assertions into your module/namespace, you can just do this:

.. code-block:: python

 from slash.assertions import *

Using the ``should`` module
---------------------------

One syntax for assertions can be done via the ``slash.should`` module:

.. autofunction:: slash.should.be

.. autofunction:: slash.should.not_be

.. autofunction:: slash.should.be_a

.. autofunction:: slash.should.not_be_a

.. autofunction:: slash.should.be_true

.. autofunction:: slash.should.be_false

.. autofunction:: slash.should.be_empty

.. autofunction:: slash.should.not_be_empty

.. autofunction:: slash.should.be_in

.. autofunction:: slash.should.not_be_in

.. autofunction:: slash.should.be_none

.. autofunction:: slash.should.not_be_none

.. autofunction:: slash.should.contain

   also known as ``contains``

.. autofunction:: slash.should.not_contain

.. autofunction:: slash.should.equal

   also known as ``equals``

.. autofunction:: slash.should.not_equal

   also known as ``not_equals``

.. autofunction:: slash.should.raise_exception

Using ``slash.assert_X`` functions
--------------------------------------

.. autofunction:: slash.assert_contains
.. autofunction:: slash.assert_not_contains

.. autofunction:: slash.assert_in
.. autofunction:: slash.assert_not_in

.. autofunction:: slash.assert_equal

   also known as ``assert_equals``
.. autofunction:: slash.assert_not_equal

   also known as ``assert_not_equals``

.. autofunction:: slash.assert_true
.. autofunction:: slash.assert_false

.. autofunction:: slash.assert_empty
.. autofunction:: slash.assert_not_empty

.. autofunction:: slash.assert_is
.. autofunction:: slash.assert_is_not

.. autofunction:: slash.assert_is_none
.. autofunction:: slash.assert_is_not_none

.. autofunction:: slash.assert_isinstance
.. autofunction:: slash.assert_not_isinstance

.. autofunction:: slash.assert_raises

