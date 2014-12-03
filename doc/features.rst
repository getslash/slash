Misc. Features
==============

Notifications
-------------

Slash provides an optional plugin for sending notifications at end of runs, via ``--with-notifications``. It supports `NMA <http://www.notifymyandroid.com/>`_, `Prowl <http://www.prowlapp.com/>`_ and `Pushbullet <https://www.pushbullet.com>`_.

To use it, specify either ``plugins.notifications.prowl_api_key``, ``plugins.notifications.nma_api_key`` or ``plugins.notifications.pushbullet_api_key`` when running. For example::

  slash run my_test.py --with-notifications -o plugins.notifications.nma_api_key=XXXXXXXXXXXXXXX

XUnit Export
------------

Pass ``--with-xunit``, ``--xunit-filenam=PATH`` to export results as xunit XMLs (useful for CI solutions and other consumers).

