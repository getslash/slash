API Documentation
=================

Testing Utilities
-----------------

.. autoclass:: slash.Test
  :members:

.. autofunction:: slash.parametrize

.. autofunction:: slash.core.fixtures.parameters.toggle

.. autofunction:: slash.core.fixtures.parameters.iterate

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

.. autofunction:: slash.register_skip_exception

Tags
----

.. autofunction:: slash.tag

Fixtures
--------

.. autofunction:: slash.fixture

.. autofunction:: slash.yield_fixture

.. autofunction:: slash.generator_fixture

.. autofunction:: slash.nofixtures()

.. autofunction:: slash.use


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

.. autofunction:: slash.plugins.register_if

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

.. autofunction:: slash.exception_handling.mark_exception
.. autofunction:: slash.exception_handling.get_exception_mark


.. autofunction:: slash.exception_handling.noswallow
.. autofunction:: slash.exception_handling.mark_exception_fatal
.. autofunction:: slash.exception_handling.get_exception_swallowing_context


Misc. Utilities
---------------

.. autofunction:: slash.repeat


Internals
---------

.. automodule:: slash.core.session
  :members:

.. automodule:: slash.runner
  :members:

.. autoclass:: slash.core.metadata.Metadata
  :members:

.. autoclass:: slash.core.result.Result
  :members:

.. autoclass:: slash.core.details.Details
  :members:
