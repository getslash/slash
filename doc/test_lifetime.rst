Test Lifetime
=============

Errors and Failures
-------------------

Almost any exception encountered during test execution is considered an *error*. 

The differentiation between errors and failures is important -- failures are specific checks that have failed, while errors are anything else. In failure cases, for instance, it is likely to encounter a meaningful description of what exactly failed (e.g. ``some_predicate()`` unexpectedly returned False). Errors are far less predictable, and can mean anything from an ``assert`` statement hidden inside your code to an ``ImportError`` or even ``SyntaxError`` when importing a module.

The :class:`.exceptions.TestFailed` exception (or any class derived from it) is used to indicate a failure. It is raised from all :ref:`assertion functions<assertions>`.

.. note:: Unlike in ``unittest``, ``AssertionError`` **DOES NOT** mean a failure, but rather an error. This is mainly because you wouldn't want internal assertions in your code and/or libraries that you use to be considered failures.

Skips
-----

Tests are considered *skipped* if the :class:`.SkipTest` exception escapes their execution. For convenience, the :func:`skip_test` function exists to raise the exception with an optional message.


.. autoclass:: shakedown.exceptions.SkipTest

.. autofunction:: shakedown.skip_test
