Test Tags
=========


Tagging Tests
-------------

Slash supports organizing tests by tagging them. This is done using the :func:`slash.tag` decorator:

.. code-block:: python
       
       @slash.tag('dangerous')
       def test_something():
           ...

You can also have tag decorators prepared in advance for simpler usage:

.. code-block:: python
       
       dangerous = slash.tag('dangerous')

       ...

       @dangerous
       def test_something():
           ...

Tags can also have values:

.. code-block:: python
       
       @slash.tag('covers', 'requirement_1294')
       def test_something():
           ...


Filtering Tests by Tags
-----------------------

When running tests you can select by tags using the ``-k`` flag. A simple case would be matching a tag substring (the same way the test name is matched::

  $ slash run tests -k dangerous

This would work, but will also select tests whose names contain the word 'dangerous'. Prefix the argument with ``tag:`` to only match tags::

  $ slash run tests -k tag:dangerous

Combined with the regular behavior of ``-k`` this yields a powrful filter::

  $ slash run tests -k 'microwave and power and not tag:dangerous'

Filtering by value is also supported::

  $ slash run test -k covers=requirement_1294

Or::

  $ slash run test -k tag:covers=requirement_1294
