Changelog
=========

* :release:`0.20.3 <10-05-2016>`
* :feature:`438` Add the register_if helper for conditionally registering hooks in plugins
* :release:`0.20.2 <03-04-2016>`
* :bug:`434` Fixed a bug where class names were not deduced properly when loading tests
* :bug:`432` Fixed a bug where session cleanups happened before ``test_end`` hooks are fired
* :release:`0.20.1 <01-03-2016>`
* :bug:`410` Fixed bug causing incorrect test frame highlighting in tracebacks
* :bug:`409` Improve session startup/shutdown logic to avoid several potentially invalid states
* :release:`0.20.0 <02-02-2016>`
* :bug:`408 major` Fix handling of cleanups registered from within cleanups
* :bug:`406 major` Fix error reporting for session scoped cleanups
* :feature:`348` Color test code differently when displaying tracebacks
* :bug:`402 major` TerminatedException now causes interactive sessions to terminate
* :feature:`405` Add ``--show-tags`` flag to ``slash list``
* :feature:`388` ``-k`` can now be specified multiple times, implying AND relationship
* :feature:`381` ``handling_exceptions`` now doesn't handle exceptions which are currently expected by ``assert_raises``
* :feature:`398` Allow specifying exc_info for add_error
* :feature:`395` Add __slash__.variation, enabling investigation of exact parametrization of tests
* :feature:`391` Add result.details, giving more options to adding/appending test details
* :feature:`386` Make slash list support -f and other configuration parameters
* :feature:`385` Add test details to xunit plugin output
* :feature:`379` Allow exception marks to be used on both exception classes and exception values
* :feature:`339` Errors in interactive session (but not ones originating from IPython input itself) are now recorded as test errors
* :release:`0.19.6 <01-12-2015>`
* :bug:`-` Minor fixes
* :release:`0.19.5 <01-12-2015>`
* :bug:`390` Fix handling of add_failure and add_error with message strings in xunit plugin
* :release:`0.19.5 <25-11-2015>`
* :bug:`389` Fix deduction of function names for parametrized tests
* :release:`0.19.3 <05-11-2015>`
* :bug:`383` Fix fixture passing to ``before`` and ``after``
* :release:`0.19.2 <13-10-2015>`
* :bug:`376` Fix xunit bug when using skip decorators without reasons
* :release:`0.19.1 <01-10-2015>`
* :bug:`374` Fix issue with xunit plugin
* :release:`0.19.0 <30-09-2015>`
* :bug:`373 major` Fix test collection progress when outputting to non-ttys
* :feature:`361` Demote slash logs to TRACE level
* :feature:`368` add slash list-config command
* :feature:`366` Added ``activate_later`` and ``deactivate_later`` to the plugin manager, allowing plugins to be collected into a 'pending activation' set, later activated with ``activate_pending_plugins``
* :feature:`366` ``--with-X`` and ``--without-X`` don't immediately activate plugins, but rather use ``activate_later`` / ``deactivate_later``
* :feature:`366` Added ``configure`` hook which is called after command-line processing but before plugin activation
* :feature:`371` Add warning_added hook
* :feature:`349` Plugin configuration is now installed in the installation phase, not activation phase
* :release:`0.18.2 <30-09-2015>`
* :bug:`372` Fixed logbook compatibility issue
* :release:`0.18.1 <11-08-2015>`
* :bug:`350` Fixed scope mismatch bug when hooks raise exceptions
* :release:`0.18.0 <02-08-2015>`
* :feature:`347` Add slash.context.fixture to point at the 'this' variable of the currently computing fixture
* :feature:`335` Add 'needs' and 'provides' to plugins, to provide fine-grained flow control over plugin calling
* :feature:`321` add Error.mark_fatal() to enable calls to mark_fatal right after add_error
* :feature:`295` SIGTERM handling for stopping sessions gracefully
* :feature:`279` Add option to silence manual add_error tracebacks (``-o show_manual_errors_tb=no``)
* :bug:`341 major` Make sure tests are garbage collected after running
* :feature:`233` slash.parametrize: allow argument tuples to be specified
* :feature:`337` Set tb level to 2 by default
* :feature:`333` Allow customization of console colors
* :feature:`332` Add ability to filter by test tags - you can now filter with ``-k tag:sometag``, ``-k sometag=2`` and ``-k "not sometag=3"``
* :feature:`240` Add support for test tags
* :feature:`324` Add test for cleanups with fatal exceptions
* :bug:`329 major` handling_exceptions(swallow=True) now does not swallow SkipTest exceptions
* :bug:`322 major` Refactored a great deal of the test running logic for easier maintenance and better solve some corner cases
* :bug:`322 major` Fix behavior of skips thrown from cleanup callbacks
* :bug:`320 major` Fix scope mechanism to allow cleanups to be added from test_start hooks
* :feature:`319` Add class_name metadata property for method tests
* :release:`0.17.0 <29-06-2015>`
* :feature:`314` Added :func:`Session.get_total_num_tests <slash.core.session.Session.get_total_num_tests>` for returning the number of tests expected to run in a session
* :feature:`312` Add before_session_start hook
* :feature:`311` Support plugin methods avoiding hook registrations with ``registers_on(None)``
* :feature:`308` Support registering private methods in plugins using ``registers_on``
* :release:`0.16.1 <17-06-2015>`
* :bug:`-` fix strict emport dependency
* :release:`0.16.0 <20-05-2015>`
* :feature:`307` Interactive test is now a first-class test and allows any operation that is allowed from within a regular test
* :feature:`306` Allow class variables in plugins
* :feature:`300` Add `log.unified_session_log` flag to make session log contain all logs from all tests
* :release:`0.15.0 <28-04-2015>`
* :feature:`289` Added ``get_config`` optional method to plugins, allowing them to supplement configuration to ``config.root.plugin_config.<plugin_name>``
* :feature:`282` Better handling of fixture dependency cycles
* :feature:`286` Better handling of unrun tests when using `x` or similar. Count of unrun tests is now reported instead of detailed console line for each unrun test.
* :feature:`267` Scoped cleanups: associate errors in cleanups to their respective result object. This means that errors can be added to tests after they finish from now on.
* :feature:`170` Add optional ``scope`` argument to ``add_cleanup``, controlling when the cleanup should take place
* :feature:`280` Add optional message argument to ``assert_raises``
* :feature:`274` Add optional separation between console log format and file log format
* :feature:`275` Add get_no_deprecations_context to disable deprecation messages temporarily
* :feature:`271` Add passthrough_types=TYPES parameter to handling_exceptions context
* :release:`0.14.3 <31-03-2015>`
* :bug:`288` Fixed accidental log file line truncation
* :release:`0.14.2 <29-03-2015>`
* :bug:`285` Fixed representation of fixture values that should not be printable (strings with slashes, for instance)
* :release:`0.14.1 <04-03-2015>`
* :bug:`270` Fixed handling of directory names and class/method names in suite files
* :release:`0.14.0 <03-03-2015>`
* :feature:`269` Add option to specify suite files within suite files
* :feature:`268` Treat relative paths listed in suite files (-f) relative to the file's location
* :feature:`-` start_interactive_shell now automatically adds the contents of slash.g to the interactive namespace
* :feature:`257` ``slash fixtures`` is now ``slash list``, and learned the ability to list both fixtures and tests
* :feature:`263` Support writing colors to log files
* :feature:`264` Allow specifying location of .slashrc via configuration
* :release:`0.13.0 <22-02-2015>`
* :feature:`261` Added a traceback to manually added errors (throush ``slash.add_error`` and friends)
* :feature:`258` Added ``hooks.error_added``, a hook that is called when an error is added to a test result or to a global result. Also works when errors are added after the test has ended. 
* :feature:`140` Added ``--repeat-each`` command line argument to repeat each test multiple times
* :feature:`249` Added @slash.repeat decorator to repeat tests multiple times
* :feature:`-` Slash now emits a console message when session_start handlers take too long
* :release:`0.12.0 <01-02-2015>`
* :feature:`177` Added 'slash fixtures' command line utility to list available fixtures
* :feature:`-` Add ``slash.session.reporter.report_fancy_message``
* :release:`0.11.0 <06-01-2015>`
* :feature:`226` Implemented ``slash.hooks.before_test_cleanups``.
* :feature:`220` ``slash.add_cleanup`` no longer receives arbitrary positional args or keyword args. The old form is still allowed for now but issues a deprecation warning.
* :feature:`211` Added ``log.last_session_dir_symlink`` to create symlinks to log directory of the last run session
* :release:`0.10.0 <15-12-2014>`
* :feature:`214` Added ``slash.nofixtures`` decorator to opt out of automatic fixture deduction.
* :feature:`16` Added ``slash.requires`` decorator to formally specify test requirements
* :feature:`209` Test cleanups are now called before fixture cleanups
* :feature:`203` Group result output by tests, not by error type
* :feature:`199` A separate configuration for traceback verbosity level (``log.traceback_level``, also controlled via ``--tb=[0-5]``)
* :feature:`196` Add 'slash version' to display current version
* :feature:`189` add add_success_only_cleanup
* :release:`0.9.3 <1-12-2014>`
* :bug:`204` Fixed a console formatting issue causing empty lines to be emitted without reason
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


