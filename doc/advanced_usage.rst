.. _advanced:

Advanced Use Cases
==================

Customizing via Setuptools Entry Points
---------------------------------------

Slash can be customized globally, meaning anyone who will run ``slash run`` or similar commands will automatically get a customized version of Slash. This is not always what you want, but it may still come in handy.

To do this we write our own customization function (like we did in `the section about customization <customize>`):

.. code-block:: python

 def cool_customization_logic():
     ... # install plugins here, change configuration, etc...


To let slash load our customization on startup, we'll use a feature of ``setuptools`` called *entry points*. This lets us register specific functions in "slots", to be read by other packages. We'll append the following to our ``setup.py`` file:

.. code-block:: python

 # setup.py
 
 ...
 setup(...
    # ...
    entry_points = {
        "slash.site.customize": [
            "cool_customization_logic = my_package:cool_customization_logic"
            ]
        },
    # ...
 )

.. note:: You can read more about setuptools entry points `here <http://stackoverflow.com/questions/774824/explain-python-entry-points>`_.

Now Slash will call our customize function when loading.

Customizing from Other Sources
------------------------------

In addition to entry points, Slash looks for other locations to load code on startup. These can sometimes be used for customization as well.

**slashrc file**
  If the file ``~/.slash/slashrc`` exists, it is loaded and executed as a regular Python file by Slash on startup.

**SLASH_SETTINGS**
  If an environment variable named ``SLASH_SETTINGS`` exists, it is assumed to point at a file path or URL to laod as a regular Python file on startup.



