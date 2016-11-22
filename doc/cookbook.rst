Cookbook
========

Controlling Test Execution Order
--------------------------------

Slash offers a hook called ``tests_loaded`` which can be used, among else, to control the test execution order. Tests are sorted by a dedicated key in their metadata (a.k.a the ``__slash__`` attribute), which defaults to the discovery order. You can set your hook registration to modify the tests as you see fit, for instance to reverse test order:

.. code-block:: python

       @slash.hooks.tests_loaded.register
       def tests_loaded(tests):
	   for index, test in enumerate(reversed(tests)):
	       test.__slash__.set_sort_key(index)

The above code is best placed in a ``slashconf.py`` file at the root of your test repository.
