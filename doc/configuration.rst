.. _configuration:

Configuration
=============

Slash uses a hierarchical configuration structure provided by `Confetti <https://github.com/vmalloc/confetti>`_. The configuration values are addressed by their full path (e.g. ``debug.enabled``, meaning the value called 'enabled' under the branch 'debug').

.. note:: You can inspect the current paths, defaults and docs for Slash's configuration via the ``slash list-config`` command from your shell

Several ways exist to modify configuration values.

Overriding Configuration Values via Command-Line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When running tests via ``slash run``, you can use the ``-o`` flag to override configuration values::

    $ slash run -o hooks.swallow_exceptions=yes ...

.. note:: Configuration values get automatically converted to their respective types. More specifically, boolean values also recognize ``yes`` and ``no`` as valid values.

Customization Files
~~~~~~~~~~~~~~~~~~~

There are several locations in which you can store files that are to be automatically executed by Slash when it runs. These files can contain code that overrides configuration values:

**slashrc file**
  If the file ``~/.slash/slashrc`` (See :ref:`conf.run.user_customization_file_path`) exists, it is loaded and executed as a regular Python file by Slash on startup.

**SLASH_SETTINGS**
  If an environment variable named ``SLASH_SETTINGS`` exists, it is assumed to point at a file path or URL to laod as a regular Python file on startup.

Each of these files can contain code which, among other things, can modify Slash's configuration. The configuration object is located in ``slash.config``, and modified through ``slash.config.root`` as follows:

.. code-block:: python

		# ~/.slash/slashrc contents
		import slash

		slash.config.root.debug.enabled = False


List of Available Configuration Values
--------------------------------------

.. config_doc:: 


