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
  If the file ``~/.slash/slashrc`` (See :ref:`conf.run.user_customization_file_path`) exists, it is loaded and executed as a regular Python file by Slash on startup.

**SLASH_SETTINGS**
  If an environment variable named ``SLASH_SETTINGS`` exists, it is assumed to point at a file path or URL to laod as a regular Python file on startup.


Loading and Running Tests in Code
---------------------------------

Sometimes you would like to run a sequence of tests that you control in fine detail, like checking various properties of a test before it is being loaded and run. This can be done in many ways, but the easiest is to use the test loader explicitly. 

.. code-block:: python

 import slash

 if __name__ == "__main__":
     with slash.Session():
          slash.run_tests(slash.loader.Loader().iter_paths(["/my_path", ...]))

The parameter given above to :func:`.run_tests` is merely an iterator yielding runnable tests. You can interfere or skip specific tests quite easily:

.. code-block:: python

 import slash
 ...
 def _filter_tests(iterator):
     for test in iterator:
          if "forbidden" in test.__slash__.fqn.path:
              continue
          yield test

 ...
     slash.run_tests(_filter_tests(slash.loader.Loader().iter_paths(...)))

.. seealso:: :ref:`Test Metadata <test_metadata>`

.. seealso:: :ref:`building_solution`
