Assertions
==========

*Shakedown* uses assertions to perform test logic. Unlike ``unittest``, assertions in Shakedown are global functions rather than methods.

Another big difference from ``unittest`` is the fact that *failed assertions don't raise ``AssertionError``s* -- they raise :class:`TestFailed`, which derives from ``AssertionError``. Since the code you'll be testing might have ``assert`` statements embedded inside, it is important to differentiate real (test) assertions from in-code assertions. 

There are several ways to perform assertions, and many assertion functions have aliases for greater readability in code, as described below.

Using the ``should`` module
---------------------------

One syntax for assertions can be done via the ``shakedown.should`` module:

.. autofunction:: shakedown.should.be

.. autofunction:: shakedown.should.not_be

.. autofunction:: shakedown.should.be_a

.. autofunction:: shakedown.should.not_be_a

.. autofunction:: shakedown.should.be_true

.. autofunction:: shakedown.should.be_false

.. autofunction:: shakedown.should.be_in

.. autofunction:: shakedown.should.not_be_in

.. autofunction:: shakedown.should.be_none

.. autofunction:: shakedown.should.not_be_none

.. autofunction:: shakedown.should.contain

   also known as ``contains``

.. autofunction:: shakedown.should.not_contain

.. autofunction:: shakedown.should.equal

   also known as ``equals``

.. autofunction:: shakedown.should.not_equal

   also known as ``not_equals``

.. autofunction:: shakedown.should.raise_exception

Using ``shakedown.assert_X`` functions
--------------------------------------

.. autofunction:: shakedown.assert_contains
.. autofunction:: shakedown.assert_not_contains

.. autofunction:: shakedown.assert_in
.. autofunction:: shakedown.assert_not_in

.. autofunction:: shakedown.assert_equal

   also known as ``assert_equals``
.. autofunction:: shakedown.assert_not_equal

   also known as ``assert_not_equals``

.. autofunction:: shakedown.assert_true
.. autofunction:: shakedown.assert_false

.. autofunction:: shakedown.assert_is
.. autofunction:: shakedown.assert_is_not

.. autofunction:: shakedown.assert_is_none
.. autofunction:: shakedown.assert_is_not_none

.. autofunction:: shakedown.assert_isinstance
.. autofunction:: shakedown.assert_not_isinstance

.. autofunction:: shakedown.assert_raises
