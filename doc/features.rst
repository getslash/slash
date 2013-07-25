Misc. Features
==============

Notifications
-------------

Slash provides an optional plugin for sending notifications at end of runs, via ``--with-notifications``. It supports `NMA <http://www.notifymyandroid.com/>`_ and `Prowl <http://www.prowlapp.com/>`_.

To use it, specify either ``notifications.prowl_api_key`` or ``notifications.nma_api_key`` when running. For example::

  slash run my_test.py --with-notifications -o notifications.nma_api_key=XXXXXXXXXXXXXXX

XUnit Export
------------

Pass ``--with-xunit``, ``--xunit-filenam=PATH`` to export results as xunit XMLs (useful for CI solutions and other consumers).

