.. _logging:

Logging
=======

As mentioned in :ref:`the introductory section <tour>`, logging in Slash is done by Logbook. The path to which logs are written is controlled with the ``-l`` flag and console verbosity is controlled with ``-v``/``-q``. Below are some more advanced topics which may be relevant for extending Slash's behavior.

Controlling Console Colors
--------------------------

Console logs are colorized according to their level by default. This is done using Logbook's colorizing handler. In some cases you might want logs from specific sources to get colored differently. This is done using :func:`slash.log.set_log_color`:

.. code-block:: python

    >>> import slash.log
    >>> import logbook
    >>> slash.log.set_log_color('my_logger_name', logbook.NOTICE, 'red')

.. note:: Available colors are taken from **logbook**. Options are "black", "darkred", "darkgreen", "brown", "darkblue", "purple", "teal", "lightgray", "darkgray", "red", "green", "yellow", "blue", "fuchsia", "turquoise", "white"

.. note:: You can also colorize log fiels by setting the :ref:`conf.log.colorize` configuration variable to ``True``

Controlling the Log Subdir Template
-----------------------------------

The filenames created under the root are controlled with the :ref:`conf.log.subpath` config variable, which can be also a format string receiving the *context* variable from slash (e.g. ``sessions/{context.session.id}/{context.test.id}/logfile.log``).


Test Ordinals
~~~~~~~~~~~~~

You can use :attr:`slash.core.metadata.Metadata.test_index0` to include an ordinal prefix in log directories, for example setting :ref:`conf.log.subpath` to:: 

    {context.session.id}/{context.test.__slash__.test_index0:03}-{context.test.id}.log

Timestamps
~~~~~~~~~~

The current timestamp can also be used when formatting log paths. This is useful if you want to create log directories named according to the current date/time::

  logs/{timestamp:%Y%m%d-%H%M%S}.log

The Session Log
~~~~~~~~~~~~~~~

Another important config path is :ref:`conf.log.session_subpath`. In this subpath, a special log file will be kept logging all records that get emitted when there's no active test found. This can happen between tests or on session start/end.

The session log, by default, does not contain logs from tests, as they are redirected to test log files. However, setting the :ref:`conf.log.unified_session_log` to ``True`` will cause the session log to contain *all* logs from all tests.

The Highlights Log
~~~~~~~~~~~~~~~~~~

Slash allows you to configure a separate log file to receive "highlight" logs from your sessions. This isn't necessarily related to the log level, as any log emitted can be marked as a "highlight". This is particularly useful if you have infrequent operations that you'd like to track and skim occasionally.

To configure a log location for your highlight logs, set the :ref:`conf.log.highlights_subpath` configuration path. To emit a highlight log, just pass ``{'highlight': True}`` to the required log's ``extra`` dict:

.. code-block:: python
       
   slash.logger.info("hey", extra={"highlight": True})

.. tip:: The :ref:`conf.log.highlights_subpath` configuration path is treated just like other logging subpaths, and thus supports all substitutions and formatting mentioned above

.. note:: All errors emitted in a session are automatically added to the highlights log


Last Log Symlinks
-----------------

Slash can be instructed to maintain a symlink to recent logs. This is useful to quickly find the last test executed and dive into its logs.

 *  To make slash store a symlink to the last session log file, use :ref:`conf.log.last_session_symlink`
 *  To make slash store a symlink to the last session log directory, use :ref:`conf.log.last_session_dir_symlink`
 *  To make slash store a symlink to the last session log file, use :ref:`conf.log.last_test_symlink`
 *  To make slash store a symlink to the last session log file, use :ref:`conf.log.last_failed_symlink`


Both parameters are strings pointing to the symlink path. In case they are relative paths, they will be computed relative to the log root directory (see above).

The symlinks are updated at the beginning of each test run to point at the recent log directory.

Silencing Logs
--------------

In certain cases you can silence specific loggers from the logging output. This is done with the :ref:`conf.log.silence_loggers` config path::

  slash run -i -o "log.silence_loggers=['a','b']"

Changing Formats
----------------

The :ref:`conf.log.format` config path controls the log line format used by slash::

    $ slash run -o log.format="[{record.time:%Y%m%d}]- {record.message}" ...
