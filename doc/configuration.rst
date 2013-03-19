Configuration
=============

Shakedown's Configuration
-------------------------

Shakedown uses a hierarchical configuration structure provided by `Confetti <https://github.com/vmalloc/confetti>`_. The root structure exists in the ``shakedown/conf.py`` file, and is generally importable by issuing::

    from shakedown.conf import config

Overriding Configuration
------------------------

When running tests via ``shake run``, you can use the ``-o`` flag to override settings externally::

    $ shake run -o hooks.swallow_exceptions=yes ...

List of Available Configuration Values
--------------------------------------

.. config_doc:: 


