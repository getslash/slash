.. _slash_run:

Running Tests
=============

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

Lines in suite files can optionally contain filters and repeat directive.

Filter allows restricting the tests actually loaded from them::

  # my_suite_file.txt
  # this is the first test file
  /path/to/tests.py
  # when running the following file, tests with "dangerous" in their name will not be loaded
  /path/to/other_tests.py # filter: not dangerous

.. seealso:: The filter syntax is exactly like ``-k`` described below

Repeat allows to repeat a line::

  # my_suite_file.txt
  # the next line will be repeated twice
  /path/to/other_tests.py # repeat: 2
  # you can use filter and repeat together
  /path/to/other_tests.py # filter: not dangerous, repeat: 2


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

Running Interactively
---------------------

As a part of the development cycle, it is often useful or even necessary to run your infrastructure in interactive mode. This allows users to experiment with your framework and learn how to use it.

Slash supports running interactively out-of-the-box, using the ``-i`` flag to ``slash run``::

  $ slash run -i

This will invoke an interactive IPython shell, initialized with your project's environment (and, of course, a valid Slash session).

By default, the namespace in which the interactive test runs contains all content of the ``slash.g`` global container. You can disable this behavior by setting :ref:`conf.interactive.expose_g_globals` to ``False``.

.. seealso:: :ref:`cookbook-interactive-namespace`


Resuming Previous Sessions
--------------------------

When you run a session that fails, Slash automatically saves the tests intended to be run for later reference. For quickly retrying a previously failed session, skipping tests which had already passed, you can use ``slash resume``::

  $ slash resume -vv <session id>

This command receives all flags which can be passed to ``slash run``, but receives an id of a previously run session for resuming.


Rerunning Previous Sessions
---------------------------

You can rerun all the tests of a previous session, given the session's tests were reported. This might be helpful when reproducing a run of specific worker, for example. You can use ``slash rerun``::

  $ slash rerun -vv <session id>

This command receives all flags which can be passed to ``slash run``, but receives an id of a previously run session for rerunning.
