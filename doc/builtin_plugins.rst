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

The notifications plugin allows users to be notified when sessions end in various methods, or notification mediums.

To use it, run Slash with ``--with-notifications``. Please notice that each notification type requires additional configuration values. You will also have to enable your desired backend with ``--notify-<backend name>`` (e.g. ``--notify-email``)

For e-mail notification, you'll need to configure your SMTP server, and pass the recipients using ``--email-to``::

  $ slash run --notify-email --with-notifications -o plugin_config.notifications.email.smtp_server='my-smtp-server.com --email-to youremail@company.com'

For using Slack notification, you should firstly configure `slack webhook integration <https://api.slack.com/incoming-webhooks>`_. And run slash::

  $ slash run --with-notifications -o plugin_config.notifications.slack.url='your-webhook-ingetration-url' -o plugin_config.notifications.slack.channel='@myslackuser'

XUnit
-----

The xUnit plugin outputs an XML file when sessions finish running. The XML conforms to the xunit format, and thus can be read and processed by third party tools (like CI services, for example)

Use it by running with ``--with-xunit`` and by specifying the output filename with ``--xunit-filename``::

  $ slash run --with-xunit --xunit-filename xunit.xml
