.. _unit_testing:

Unit Testing Slash
==================

The following information is intended for anyone interested in developing Slash or adding new features, explaining how to effectively use the unit testing facilities used to test Slash itself.


The Suite Writer
----------------

The unit tests use a dedicated mechanism allowing creating a virtual test suite, and then easily writing it to a real directory, run it with Slash, and introspect the result.

The suite writer is available from ``tests.utils.suite_writer``:

.. code-block:: python
       
       >>> from tests.utils.suite_writer import Suite
       >>> suite = Suite()


Basic Usage
~~~~~~~~~~~

Add tests by calling ``add_test()``. By default, this will pick a different test type (function/method) every time.

.. code-block:: python
       
       >>> for i in range(10):
       ...     test = suite.add_test()

The created **test object** is not an actual test that can be run by Slash -- it is an object representing a future test to be created. The test can later be manipulated to perform certain actions when run or to expect things when run.

The simplest thing we can do is run the suite:

.. code-block:: python
       
       >>> summary = suite.run()
       >>> len(summary.session.results)
       10
       >>> summary.ok()
       True

We can, for example, make our test raise an exception, thus be considered an error:

.. code-block:: python
       
       >>> test.when_run.raise_exception()

Noe let's run the suite again (it will commit itself to a new path so we can completely diregard the older session):

.. code-block:: python
       
       >>> summary = suite.run()
       >>> summary.session.results.get_num_errors()
       1
       >>> summary.ok()
       False

The suite writer already takes care of verifying that the errored test is actually reported as error and fails the run.


Adding Parameters
~~~~~~~~~~~~~~~~~

To test parametrization, the suite write supports adding parameters and fixtures to test. First we will look at parameters (translating into ``@slash.parametrize`` calls):

.. code-block:: python

       >>> suite.clear()
       >>> test = suite.add_test()
       >>> p = test.add_parameter()
       >>> len(p.values)
       3
       >>> suite.run().ok()
       True

Adding Fixtures
~~~~~~~~~~~~~~~

Fixtures are slightly more complex, since they have to be added to a file first. You can create a fixture at the file level:

.. code-block:: python

       >>> suite.clear()
       >>> test = suite.add_test()

       >>> f = test.file.add_fixture()
       >>> _ = test.depend_on_fixture(f)
       >>> suite.run().ok()
       True

Fixtures can also be added to the ``slashconf`` file:

.. code-block:: python
       
       >>> f = suite.slashconf.add_fixture()

Fixtures can depend on each other and be parametrized:

.. code-block:: python
       
       >>> suite.clear()
       >>> f1 = suite.slashconf.add_fixture()
       >>> test = suite.add_test()
       >>> f2 = test.file.add_fixture()
       >>> _ = f2.depend_on_fixture(f1)
       >>> _ = test.depend_on_fixture(f2)
       >>> p = f1.add_parameter()
       >>> summary = suite.run()
       >>> summary.ok()
       True
       >>> len(summary.session.results) == len(p.values)
       True

You can also control the fixture scope:

.. code-block:: python
       
       >>> f = suite.slashconf.add_fixture(scope='module')
       >>> _ = suite.add_test().depend_on_fixture(f)
       >>> suite.run().ok()
       True

And specify autouse (or implicit) fixtures:

.. code-block:: python
       
       >>> suite.clear()
       >>> f = suite.slashconf.add_fixture(scope='module', autouse=True)
       >>> t = suite.add_test()
       >>> suite.run().ok()
       True

