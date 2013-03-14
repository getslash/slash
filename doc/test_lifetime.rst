Test Lifetime
=============

Skips
-----

Tests are considered *skipped* if the :class:`.SkipTest` exception escapes their execution. For convenience, the :func:`skip_test` function exists to raise the exception with an optional message.


.. autoclass:: shakedown.exceptions.SkipTest

.. autofunction:: shakedown.skip_test
