Built-in Plugins
================

Slash comes with pre-installed, built-in plugins that can be activated when needed.

Coverage
--------

This plugins tracks and reports runtime code coverage during runs, and reports the results in various formats. It uses the Net Batchelder's `coverage package <https://coverage.readthedocs.io/en/>`_.

To use it, run Slash with ``--with-coverage``, and optionally specify modules to cover::

  $ slash run --with-coverage --cov mypackage --cov-report html

Notifications
-------------

*STUB*


XUnit
-----

The xUnit plugin outputs an XML file when sessions finish running. The XML conforms to the xunit format, and thus can be read and processed by third party tools (like CI services, for example)

Use it by running with ``--with-xunit`` and by specifying the output filename with ``--xunit-filename``::

  $ slash run --with-xunit --xunit-filename xunit.xml
