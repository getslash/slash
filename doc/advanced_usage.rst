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


Loading and Running Tests in Code
---------------------------------

Sometimes you would like to run a sequence of tests that you control in fine detail, like checking various properties of a test before it is being loaded and run. This can be done in many ways, but the easiest is to use the test loader explicitly. 

.. code-block:: python

 import slash

 if __name__ == "__main__":
     with slash.Session() as s:
         tests = slash.loader.Loader().get_runnables(["/my_path", ...])
         with s.get_started_context():
             slash.run_tests(tests)

The parameter given above to :func:`slash.runner.run_tests` is merely an iterator yielding runnable tests. You can interfere or skip specific tests quite easily:

.. code-block:: python

 import slash
 ...
 def _filter_tests(iterator):
     for test in iterator:
          if "forbidden" in test.__slash__.file_path:
              continue
          yield test

 ...
     slash.run_tests(_filter_tests(slash.loader.Loader().get_runnables(...)))

.. seealso:: :ref:`Test Metadata <test_metadata>`

.. seealso:: :ref:`customizing`

Specifying Default Test Source for ``slash run``
------------------------------------------------

.. _default_test_source:


If you use ``slash run`` for running your tests, it is often useful to specify a default for the test path to run. This is useful if you want to provide a sane default running environment for your users via a ``.slashrc`` file. This can be done with the :ref:`conf.run.default_sources` configuration option:

.. code-block:: python

    # ...
    slash.config.root.run.default_sources = ["/my/default/path/to/tests"]


