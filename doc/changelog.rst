Changelog
=========

* :release:`0.9.2 <24-11-2014>`
* :bug:`198` fix test_methodname accidentally starting with a dot
* :release:`0.9.1 <30-10-2014>`
* :release:`0.9.0 <30-10-2014>`
* :feature:`194` add assert_almost_equal
* :feature:`190` Support __slash__.test_index0 and __slash__.test_index1 for easier enumeration in logs
* :feature:`179` Documentation overhaul
* :feature:`183` Add slash.parameters.toggle as a shortcut for iterating ``[True, False]``
* :release:`0.8.0 <12-10-2014>`
* :feature:`127` py.test style fixture support, major overhaul of tests and loading code.
* :feature:`-` removed the test contexts facility introduced in earlier versions. The implementation was partial and had serious drawbacks, and is inferior to fixtures.
* :feature:`167` Fixed erroneous behavior in which skipped tasks after using ``-x`` caused log symlinks to move
* :feature:`159` Add optional 'last failed' symlink to point to last failed test log
* :feature:`163` Added ``-k`` for selecting tests by substrings
* :feature:`162` Test loading and other setup operations now happen before ``session_start``, causing faster failing on simple errors
* :feature:`-` Log symlinks can now be relative paths (considrered relative to the logging root directory)
* :feature:`160` Add option to serialize warnings to dicts
* :release:`0.7.2 <21-08-2014>`
* :feature:`171` Add error times to console reports
* :release:`0.7.1 <14-07-2014>`
* :bug:`-` Fixed error summary reporting
* :release:`0.7.0 <07-07-2014>`
* :feature:`153` Report warnings at the end of sessions
* :feature:`152` Truncate long log lines in the console output
* :feature:`148` Detailed tracebacks now emitted to log file
* :feature:`-` Renamed ``debug_hooks`` to ``debug_hook_handlers``. Debugging hook handlers will only trigger for slash hooks.
* :feature:`137` Fixed parameter iteration across inheritence trees
* :feature:`150` Add log links to results when reporting to console
* :feature:`145` Add option to save symlinks to the last session log and last test log
* :feature:`146` Add test id and error/failure enumeration in test details
* :feature:`149` Make console logs interact nicely with the console reporter non-log output
* :feature:`144` Add option to colorize console logs in custom colors
* :release:`0.6.1 <27-05-2014>`
* :bug:`142` Allow registering plugin methods on custom hooks
* :bug:`143` Use gossip's inernal handler exception hook to debug hook failures when ``--pdb`` is used
* :release:`0.6.0 <21-05-2014>`
* :feature:`-` Added assertion introspection via AST rewrite, borrowed from `pytest <http://pytest.org>`_.
* :feature:`138` Move to `gossip <http://gossip.readthedocs.org>`_ as hook framework.
* :feature:`141` Add slash.utils.deprecated to mark internal facilities bound for removal
* :feature:`129` Overhaul rerunning logic (now called 'resume')
* :feature:`128` Slash now loads tests eagerly, failing earlier for bad imports etc. This might change in the future to be an opt-out behavior (change back to lazy loading)
* :feature:`-` Overhaul the reporting mechanism, make output more similar to py.test's, including better error reporting.
* :release:`0.5.0 <09-04-2014>`
* :feature:`132` Support for providing hook requirements to help resolving callback order (useful on initialization)
* :release:`0.4.2 <19-01-2014>`
* :release:`0.4.1 <19-01-2014>`
* :release:`0.4.0 <15-12-2013>`
* :feature:`114` Support for fatal exception marks
* :feature:`116` Support '-f' to specify one or more files containing lists of files to run
* :feature:`121` Support 'append' for CLI arguments deduced from config
* :feature:`120` Support multiple exception types in should.raise_exception
* :release:`0.3.1 <20-11-2013>`
* :feature:`115` Add session.logging.extra_handlers to enable adding custom handlers to tests and the session itself
* :release:`0.3.0 <18-11-2013>`
* :feature:`113` Add option to debug hook exceptions (-o debug.debug_hooks=yes)
* :release:`0.2.0 <20-10-2013>`
* :feature:`103` Add context.test_filename, context.test_classname, context.test_methodname
* :feature:`96` Add option to specify logging format
* :feature:`19` Add ability to add non-exception errors and failures to test results
* :release:`0.1.0 <3-9-2013>`
* :feature:`45` Add option for specifying default tests to run
* :feature:`74` Enable local .slashrc file
* :feature:`72` Clarify errors in plugins section
* :feature:`26` Support test rerunning via "slash rerun"
* :feature:`-` Coverage via coveralls
* :feature:`-` Documentation additions and enhancements
* :feature:`69` Move slash.session to slash.core.session. slash.session is now the session context proxy, as documented
* :feature:`-` Add should.be_empty, should.not_be_empty
* :feature:`75` Support matching by parameters in FQN, Support running specific or partial tests via FQN
* :release:`0.0.2 <7-7-2013>`
* :feature:`46`: Added plugin.activate() to provide plugins with the ability to control what happens upon activation
* :feature:`40`: Added test context support - you can now decorate tests to provide externally implemented contexts for more flexible setups
* :feature:`-` Renamed slash.fixture to slash.g (fixture is an overloaded term that will maybe refer to test contexts down the road)
* :feature:`48`, #54: handle import errors and improve captured exceptions
* :feature:`3` Handle KeyboardInterrupts (quit fast), added the test_interrupt hook
* :feature:`5` add_critical_cleanup for adding cleanups that are always called (even on interruptions)


