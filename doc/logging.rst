.. _logging:

Logging
=======

The Slash Logger
--------------------

Slash uses `Logbook <http://logbook.pocoo.org>`_ for logging. It has many advantages over Python's own ``logging`` package. It is strongly recommended that you use logbook for logging.

Slash exposes a global logger intended for tests, and it is recommended to use it for simple logging tasks:

.. code-block:: python

 import slash

 class SomeTest(slash.Test):
     def test_1(self):
         slash.logger.debug("Hello!")

Console Log
-----------

By default logs above **WARNING** get emitted to the console. This can be changed via the :ref:`conf.log.console_level` config variable. You can also use **-v**/**-q** to increase/decrease console verbosity accordingly.

Logging To Files
----------------

By default logs are not saved anywhere. This is easily changed.

The :ref:`conf.log.root` config variable controls the root dir for logs. Under that path log files for various tests will be created. This variable is also controlled with the ``-l`` command-line argument.

The filenames created under the root are controlled with the :ref:`conf.log.subpath` config variable, which can be also a format string receiving the *context* variable from slash (e.g. ``sessions/{context.session.id}/{context.test.id}/logfile.log``).

Another important config path is ``log.session_subpath``. In this subpath, a special log file will be kept logging all records that get emitted when there's no active test found. This can happen between tests or on session start/end.

Silencing Logs
--------------

In certain cases you can silence specific loggers from the logging output. This is done with the :ref:`conf.log.silence_loggers` config path::

  slash run -i -o "log.silence_loggers=['a','b']"

Changing Formats
----------------

The :ref:`conf.log.format` config path controls the log line format used by slash::

    $ slash run -o log.format="[{record.time:%Y%m%d}]- {record.message}" ...

