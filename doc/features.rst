Misc. Features
==============

Notifications
-------------

Shakedown provides an optional plugin for sending notifications at end of runs, via ``--with-notifications``. It supports `NMA <http://www.notifymyandroid.com/>`_ and `Prowl <http://www.prowlapp.com/>`_.

To use it, specify either ``notifications.prowl_api_key`` or ``notifications.nma_api_key`` when running. For example::

  shake run my_test.py --with-notifications -o notifications.nma_api_key=XXXXXXXXXXXXXXX


