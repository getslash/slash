Cookbook
========

Execution
---------

Controlling Test Execution Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Slash offers a hook called ``tests_loaded`` which can be used, among else, to control the test execution order. Tests are sorted by a dedicated key in their metadata (a.k.a the ``__slash__`` attribute), which defaults to the discovery order. You can set your hook registration to modify the tests as you see fit, for instance to reverse test order:

.. code-block:: python

       @slash.hooks.tests_loaded.register
       def tests_loaded(tests):
	   for index, test in enumerate(reversed(tests)):
	       test.__slash__.set_sort_key(index)

The above code is best placed in a ``slashconf.py`` file at the root of your test repository.


Logging
-------

Adding Multiple Log Files to a Single Test Result
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Slash result objects contain the main path of the log file created by Slash (if logging is properly configured for the current run).

In some cases it may be desirable to include multiple log files for the current test. This can be useful, for example, if the current test runs additional tools or processes emitting additional logs:


.. code-block:: python
       
    import slash
    import subprocess

    def test_running_validation_tool():
        log_dir = slash.context.result.get_log_dir()
        log_file = os.path.join(log_dir, "tool.log")

        slash.context.result.add_extra_log_path(log_file)

        with open(os.path.join(log_dir, "tool.log"), "w") as logfile:
            res = subprocess.run(f'/bin/validation_tool -l {log_dir}', shell=True, stdout=logfile)
            res.check_returncode()

You can also configure extre session paths, for example from plugins:

.. code-block:: python

    class MyPlugin(slash.plugins.PluginInterface):

        def get_name(self):
            return "my_plugin"

        def get_config(self):
            retrun {'extra_log_path': ''}

        def session_start(self):
            log_path = slash.config.root.plugin_config.my_plugin.extra_log_path
            if log_path:
                slash.context.session.results.global_result.add_extra_log_path(log_path)
