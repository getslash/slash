.. _slash_run:

A Closer Look at ``slash run``
==============================

The main front-end for Slash is the ``slash run`` utility, invoked from the command line. It has several interesting options worth mentioning.

By default, it receives the path to load and run tests from::

  $ slash run /path/to/tests

Verbosity
---------

Verbosity is increased with ``-v`` and decreased with ``-q``. Those can be specified multiple times.

In addition to the verbosity itself, tracebacks which are displayed at the session summary can be controlled via tha ``--tb`` flag, specifying the verbosity level of the tracebacks. ``0`` means no tracebacks, while ``5`` means the highest detail available.

.. seealso:: :ref:`logging`

Loading Tests from Files
------------------------

You can also read tests from file or files which contain paths to run. Whitespaces and lines beginning with a comment ``#`` will be ignored::

  $ slash run -f file1.txt -f file2.txt

Debugging & Failures
--------------------

Debugging is done with ``--pdb``, which invokes the best debugger available.

Stopping at the first unsuccessful test is done with the ``-x`` flag.


.. seealso:: :ref:`exceptions`



Including and Excluding Tests
-----------------------------

The ``-k`` flag to ``slash run`` is a versatile way to include or exclude tests. Provide it with a substring to only run tests containing the substring in their names::

  $ slash run -k substr /path/to/tests

Use ``not X`` to exclude any test containing **X** in their names::

  $ slash run -k 'not failing_' /path/to/tests

Or use a more complex expression involving ``or`` and ``and``::

  $ slash run -k 'not failing_ and components' /path/to/tests

The above will run all tests with ``components`` in their name, but without ``failing_`` in it.

Overriding Configuration
------------------------

The ``-o`` flag enables us to override specific paths in the configuration, properly converting their respective types::

  $ slash run -o path.to.config.value=20 ...



.. seealso:: configuration


