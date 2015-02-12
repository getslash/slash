API Documentation
=================

Testing Utilities
-----------------

.. autoclass:: slash.Test
  :members:

.. autofunction:: slash.parametrize

.. autofunction:: slash.core.fixtures.parameters.toggle

.. autofunction:: slash.abstract_test_class


Assertions
----------

.. autofunction:: slash.assert_raises

.. autofunction:: slash.assert_almost_equal

Cleanups
--------

.. autofunction:: slash.add_cleanup

.. autofunction:: slash.add_critical_cleanup

.. autofunction:: slash.add_success_only_cleanup

Skips
-----

.. autoclass:: slash.exceptions.SkipTest

.. autofunction:: slash.skipped

.. autofunction:: slash.skip_test

Fixtures
--------

.. autofunction:: slash.fixture

.. autofunction:: slash.nofixtures()


Requirements
------------

.. autofunction:: slash.requires

Warnings
--------


.. autoclass:: slash.warnings.SessionWarnings
  :members:
  :special-members: 


Hooks
-----

.. automodule:: slash.hooks
  :members:


Plugins
-------


.. autofunction:: slash.plugins.active

.. autofunction:: slash.plugins.registers_on

.. autoclass:: slash.plugins.PluginInterface
  :members:

.. autoclass:: slash.plugins.PluginManager
  :members:


Logging
-------

.. automodule:: slash.log
  :members:

Exceptions
----------

.. autofunction:: slash.exception_handling.handling_exceptions

.. autofunction:: slash.exception_handling.is_exception_marked
.. autofunction:: slash.exception_handling.mark_exception
.. autofunction:: slash.exception_handling.get_exception_mark


.. autofunction:: slash.exception_handling.noswallow
.. autofunction:: slash.exception_handling.mark_exception_fatal
.. autofunction:: slash.exception_handling.get_exception_swallowing_context


Misc. Utilities
---------------

.. autofunction:: slash.repeat(num_repetitions)

  A decorator specifying that the decorated test is to be repeated a given amount of times

Internals
---------

.. automodule:: slash.core.session
  :members:

.. automodule:: slash.runner
  :members:

.. autoclass:: slash.core.metadata.Metadata
  :members:
