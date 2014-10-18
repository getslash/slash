.. _internals:

Slash Internals
===============

The Session Object
------------------

Tests are always run in a context, called **a session**. A session is used to identify the test execution process, giving it a unique id and collecting the entire state of the run.

The :class:`.Session` represents the current test execution session, and contains the various state elements needed to maintain it. Since sessions also contain test results and statuses, trying to run tests without an active session will fail.

The currently active session is accessible through ``slash.session``:

.. code-block:: python

  from slash import session

  print("The current session id is", session.id)

.. note:: Normally, you don't have to create slash sessions programmatically. Slash creates them for you when running tests. However, it is always possible to create sessions in an interpreter:

    .. code-block:: python

        from slash import Session 

        ...
        with slash.Session() as s:
             ... # <--- in this context, s is the active session

.. _test_metadata:

Test Metadata
-------------

Each test being run contains the ``__slash__`` attribute, meant to store metadata about the test being run. 

.. note:: Slash does not save the actual test instance being run. This is important because in most cases dead tests contain reference to whole object graphs that need to be released to conserve memory. The only thing that is saved is the test metadata structure.

Test ID
~~~~~~~

Each test has a unique ID derived from the session id and the ordinal number of the test being run. This is saved as ``test.__slash__.id``.




