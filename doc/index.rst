.. Shakedown documentation master file, created by
   sphinx-quickstart on Fri Feb 22 23:34:56 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

What is Shakedown?
==================

Shakedown is a testing framework written in Python. Unlike many other testing frameworks out there, Shakedown focuses on building in-house testing solutions for large projects. 

Most testing solutions today are focused around the good old ``unittest`` framework. Although recently `renovated <https://pypi.python.org/pypi/unittest2>`_, ``unittest`` is still very strongly focused on, well, unit tests. It seems like most testing solutions just try to build a nice wrapper around discovering and running ``unittest.TestCase`` derivatives, and running them in a sequence. This, along with the set of assertion methods provided by ``unittest.TestCase``, and a little reporting logic, is indeed more than 80% of the work involved in testing.

However, it seems nobody solves the remaining 20% properly. When running a testing effort on a product or a single project (as opposed to unit testing lots of modules or components), the emphasis is different. You have to put a lot of effort adapting your framework to your ecosystem:

* How is a test execution reported? Who holds the records for execution?
* Who maintains the log files resulting from tests? 
* Who organizes the log directory structure? How do we find which log file belongs to which test?
* How do we share code between tests more elegantly?
* Where do we fetch the infrastructure code from?
* How do we identify the current user running the tests (for reporting, etc)?
* How does our framework fit into the existing organization ecosystem (bug reporting, test reporting, log collection, etc)?

All these and many more questions go unanswered in most of the solutions available today. There are many concrete examples, `covered more elaborately here <why not X>`.

Shakedown helps you achieve a coherent, robust in-house testing solution:

1. No more ``unittest.TestCase``. Execution now revolves around **runnable instances** and **runnable instance factories**. This means a lot of flexibility for the test author. All the serious hackery going on in ``unittest.TestCase.runTest`` is no more.
2. Provide a rich, hierarchical configuration mechanism which can be updated from multiple sources.
3. A strong plugin engine with support for callbacks and contextbacks (hooked context managers), allowing you to extend the framework from the outside easily.

Contents:
=========

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

