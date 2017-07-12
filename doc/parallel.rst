.. _parallel:

Parallel execution
==============================

By default, tests run in serial order. However, it is possible to run tests in parallel mode.

Using parallel, slash will run a 'parent' process that will be used as server, and a number of child processes that will execute tests.


Running in parallel mode
------------------------

In order to run tests in parallel, just add ``--parallel`` and the number of workers you want to start. For example::

  $ slash run /path/to/tests --parallel 4

will start a server and 4 workers that execute tests.
If no address and no port are specified (using ``--parallel_addr`` and ``--parallel_port``), localhost and a random port will be assigned for the server.

By default, only the server will output logs to the console. However, you can use tmux to show output from each worker::

  $ slash run /path/to/tests --parallel 4 --tmux  [--tmux-panes]

If using tmux panes, a new pane will be opened for every worker, and there its output will be. If not, each worker will open a new window.


How parallel exeuction works
----------------------------

When running slash in parallel mode, the main process will start a server and a number of workers in new processes.
The server then will wait until all the workers to connect and collect tests.
Only after all the workers connect and validate that all of them collected the same tests collection, the test execution will start:

* Each worker asks the server for a test.
* The server gives them one test to execute.
* The worker executes the test and report the server the test's results.
* The worker asks for another test and so on, until all tests are executed.
* Clients disconnect from the server, and the server terminates.

Worker session ids
-------------------

Each worker will have a session_id that starts with the servers' session_id, and ends with it's client_id.

For example, if the server's session_id is 496272f0-66dd-11e7-a4f0-00505699924f_0 and there are 2 workers, their session ids will be:

* 496272f0-66dd-11e7-a4f0-00505699924f_1
* 496272f0-66dd-11e7-a4f0-00505699924f_2
