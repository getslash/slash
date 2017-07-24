.. _parallel:

Parallel Test Execution
=======================

.. index::
   single: parallel
   double: parallel; test execution

By default, Slash runs tests sequentially through a single session
process. However, it is also possible to use Slash to run tests in
parallel. In this mode, slash will run a 'parent' session process that will be
used to distribute the tests, and a number of child session processes
that will receive the distributed tests and run them.


Running in Parallel Mode
------------------------

In order to run tests in parallel, just add ``--parallel`` and the number of workers you want to start. For example::

  $ slash run /path/to/tests --parallel 4

If, for instance, most of your tests are CPU-bound, it would make
sense to run them like this::

  $ slash run /path/to/tests --parallel $(nproc)

to use a single worker per CPU core.

.. note:: The parallel mechanism works by listening on a local TCP
          socket, to which the worker session processes connect and
          receive test descriptions via RPC. In case you want, you can
          control the address and/or port settings via the
          ``--parallel-addr`` and ``--parallel-port`` command-line arguments.

By default, only the paerent session process outputs logs to the
console. For a more controlled run you can use ``tmux`` to run your
workers, so that you can examine their outputs::

  $ slash run /path/to/tests --parallel 4 --tmux  [--tmux-panes]

If ``--tmux-panes`` is specified, a new pane will be opened for every worker, letting it
emit console output. Otherwise each worker will open a new window.


The Parallel Execution Mechanism
--------------------------------

When running Slash in parallel mode, the main process starts a server and a number of workers as new processes.
The server then waits until all the workers connect and start collecting tests.
Only after all the workers connect and validate that all of them collected the same tests collection, the test execution will start:

* Each worker asks the master process for a test.
* The master process gives them one test to execute.
* The worker executes the test and reports the test's results to the parent.
* The worker asks for the next test and so on, until all tests are executed.
* The worker processes disconnect from the server, and the server
  terminates.

Worker session ids
-------------------

Each worker will have a session_id that starts with the servers' session_id, and ends with it's client_id.

For example, if the server's session_id is 496272f0-66dd-11e7-a4f0-00505699924f_0 and there are 2 workers, their session ids will be:

* 496272f0-66dd-11e7-a4f0-00505699924f_1
* 496272f0-66dd-11e7-a4f0-00505699924f_2
