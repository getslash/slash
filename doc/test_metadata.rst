.. _test_metadata:

Test Metadata
=============

Each test being run contains the ``__slash__`` attribute, meant to store metadata about the test being run. 

.. note:: Slash does not save the actual test instance being run. This is important because in most cases dead tests contain reference to whole object graphs that need to be released to conserve memory. The only thing that is saved is the test metadata structure.

Test ID
-------

Each test has a unique ID derived from the session id and the ordinal number of the test being run. This is saved as ``test.__slash__.id``.

Test FQN
--------

When a test is being run it receives a *fully qualified name*, or FQN, identifying it. It is stored in the test metadata as ``test.__slash__.fqn``.

.. note:: FQNs are sometimes not really fully qualified, especially in cases where slash fails to deduce the source of the test. A good example of this is when running test classes directly in code, instead of loading them via the slash :class:`loader<slash.loader.Loader>`.




