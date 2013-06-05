.. _configuration:

Configuration
=============

Slash's Configuration
-------------------------

Slash uses a hierarchical configuration structure provided by `Confetti <https://github.com/vmalloc/confetti>`_. The root structure exists in the ``slash/conf.py`` file, and is generally importable by issuing::

    from slash.conf import config

Overriding Configuration
------------------------

When running tests via ``slash run``, you can use the ``-o`` flag to override settings externally::

    $ slash run -o hooks.swallow_exceptions=yes ...

List of Available Configuration Values
--------------------------------------

.. config_doc:: 


