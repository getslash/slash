.. _assertions:

Assertions
==========

*Slash* uses assertions to perform test logic. Unlike ``unittest``, assertions in Slash are global functions rather than methods.

Another big difference from ``unittest`` is the fact that *failed assertions don't raise ``AssertionError``s* -- they raise :class:`TestFailed`, which derives from ``AssertionError``. Since the code you'll be testing might have ``assert`` statements embedded inside, it is important to differentiate real (test) assertions from in-code assertions. 

There are several ways to perform assertions, and many assertion functions have aliases for greater readability in code, as described below.

Using the ``should`` module
---------------------------

One syntax for assertions can be done via the ``slash.should`` module:

.. autofunction:: slash.should.be

.. autofunction:: slash.should.not_be

.. autofunction:: slash.should.be_a

.. autofunction:: slash.should.not_be_a

.. autofunction:: slash.should.be_true

.. autofunction:: slash.should.be_false

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

.. autofunction:: slash.assert_is
.. autofunction:: slash.assert_is_not

.. autofunction:: slash.assert_is_none
.. autofunction:: slash.assert_is_not_none

.. autofunction:: slash.assert_isinstance
.. autofunction:: slash.assert_not_isinstance

.. autofunction:: slash.assert_raises
