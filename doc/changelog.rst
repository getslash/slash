Changelog
=========

* :release:`1.6.4 <19-7-2018>`
* :bug:`820` Fix error handling when capturing distilled tracebacks
* :release:`1.6.3 <15-7-2018>`
* :release:`1.6.1 <1-7-2018>`
* :bug:`-` Fix support for Python 3.7
* :release:`1.6.0 <6-5-2018>`
* :feature:`771` Keyword arguments to ``registers_on`` now get forwarded to Gossip's ``register`` API
* :feature:`769` Added a new configuration flag, ``log.show_raw_param_values``, defaulting to ``False``. If set to True, log lines for beginnings of tests will contain actual parametrization values instead of format-safe strings.
* :feature:`528` ``slash.exclude`` can now exclude combinations of parameter values
* :bug:`783` Session errors in children are now handled and reported when running with parallel
* :feature:`785` Plugins can now be marked to indicate whether or not they support parallel
  execution, using ``slash.plugins.parallel_mode``. To avoid errors, Slash assumes that unmarked
  plugins do not support parallel execution.
* :feature:`779` Added ``config.root.run.project_name``, which can be configured to hold the name of the current project. It defaults to the name of the directory in which your project's .slashrc is located
* :bug:`772 major` Fix handling exceptions which raised from None in interactive session
* :feature:`782` Added new hooks: ``before_session_cleanup``, ``after_session_end``
* :release:`1.5.1 <10-3-2018>`
* :bug:`767` Fixed traceback variable capture for cases where ``self=None``
* :release:`1.5.0 <7-3-2018>`
* :feature:`590` Add support for labeling parametrization variations
* :feature:`697` Added ``slash.before_interactive_shell`` hook
* :feature:`-` Added a configuration option preventing ``slash.g`` from being available in interactive namespaces
* :feature:`664` Added ``metadata.set_file_path``, allowing integrations to set a custom file path to be associated with a loaded test
* :feature:`752` Added ``slash.ignore_warnings`` to filter unwanted warnings during sessions
* :feature:`757` ``slash list tests`` now accepts the ``--warnings-as-errors`` flag, making it treat warnings it encounters as errors
* :feature:`755` ``timestamp`` can now be used when formatting log path names
* :feature:`747` session.results.global_result.is_success() now returns False if any test in the session isn't successful
* :feature:`-` Add ``slash rerun`` - given a session_id, run all the tests of this session
* :feature:`740` session.results.current is now a complete synonym for slash.context.result
* :feature:`702` Rename log.traceback_level to log.console_traceback_level
* :feature:`681` Added a new hook, ``log_file_closed``, and added configuration ``log.cleanup`` to enable removing log files after they are closed
* :feature:`719` Added log.core_log_level, allowing limiting the verbosity of logs initiated from Slash itself
* :feature:`-` ``-X`` can now be used to turn off stop-on-error behavior. Useful if you have it on by default through a configuration file
* :feature:`711` Logs can now optionally be compressed on-the-fly through the ``log.compression.enabled`` configuration parameter
* :feature:`723` Add configuration for resume state path location
* :bug:`721 major` Add timeout to sending emails through SMTP
* :feature:`-` Support fixture keyword arguments for ``generator_fixture``
* :feature:`712` Added ``--pdb-filter`` - a new command-line flag that allows the user to enter pdb only on specific caught exceptions, based on pattern matching (similar to ``-k``)
* :bug:`714 major` Session cleanups now happen under the global result object
* :bug:`669 major` Session-scoped fixtures now properly register cleanups on session scope as expected
* :bug:`710 major` Fix sorting when repeat-all option is use
* :feature:`698` By setting ``log.traceback_variables`` to ``True``, traceback variable values will now be written to the debug log upon failures/errors
* :feature:`704` Error objects now have their respective ``exc_info`` attribute containing the exception info for the current info (if available). This deprecates the use of the ``locals``/``globals`` attributes on traceback frames.
* :feature:`-` During the execution of ``error_added`` hooks, traceback frame objects now have ``python_frame``, containing the original Pythonic frame that yielded them. Those are cleared soon after the hook is called.
* :feature:`-` Suite files can now have a ``repeat: X`` marker to make the test run multiple times (Thanks @pierreluctg!)
* :bug:`671 major` Help for ``slash resume`` is now more helpful
* :feature:`685` use.X is now a shortcut for use('x') for fixture annotations
* :feature:`692` Enhance errors summary log to session highlights log (configuration changed: ``log.errors_subpath`` -> ``log.highlights_subpath``)
* :feature:`658` Deprecate ``PluginInterface.get_config()`` and rename it to ``PluginInterface.get_default_config()``
* :bug:`- major` Fix tests loading order for some FS types
* :feature:`689` Added a new hook, ``interruption_added``, for registering exceptions which cause test/session interruptions
* :feature:`686` ``assert_raises`` raises ``ExpectedExceptionNotCaught`` if exception wasn't caught also allowing inspection of the expected exception object
* :bug:`684 major` Optimize test loading with ``--repeat-each`` and ``--repeat-all``
* :bug:`679 major` Fix coloring console for non TTY stdout
* :feature:`675` Emit native python warnings for logbook warning level
* :feature:`661` Support PDB notifications by notifications plugin
* :feature:`660` Add configuration for notifications plugin ``--notify-only-on-failure``
* :feature:`662` Change email notification icon based on session success status
* :release:`1.4.6 <3-12-2017>`
* :bug:`701` Fixed error in coverage reporter cleanup
* :bug:`700` Fixed handling of non-exception errors in session scope
* :release:`1.4.3 <14-9-2017>`
* :bug:`670` Improve handling of interruption exceptions - custom interruption exceptions will now properly cause the session and test to trigger the ``session_interrupt`` and ``test_interrupt`` hooks. Unexpected exceptions like ``SystemExit`` from within tests are now also reported properly instead of silently ignored
* :bug:`668` Properly initialize colorama under Windows
* :bug:`665` Support overriding notifications plugin's ``from_email`` by configuration
* :release:`1.4.2 <13-8-2017>`
* :bug:`-` Add ``current_config`` property to plugins
* :release:`1.4.1 <9-8-2017>`
* :bug:`-` Add ability to include details in email notifications
* :bug:`-` Restore default enabled state for Prowl/NMA/Pushbullet notifications
* :release:`1.4.0 <8-8-2017>`
* :feature:`-` Added new hook ``prepare_notification`` to process notifications before being sent by the notifications plugin
* :feature:`662` Improve notifications plugin, add support for email notifications
* :feature:`651` Add ``host_fqdn`` and ``host_name`` attributes to session
* :feature:`647` Support internal plugins
* :feature:`647` Support installing plugins as "internal" -- thus not letting users disable or enable them through the command line
* :release:`1.3.0 <24-07-2017>`
* :feature:`213` Added parallel execution capability (still considered experimental) - tests can be run in parallel by multiple subprocess "workers". See `the documentation <http://slash.readthedocs.io/en/master/parallel.html>`_ for more information
* :feature:`596` Slash now supports a flag to disable assertion introspection on assertions containing messages (``run.message_assertion_introspection``)
* :feature:`642` Support multiple registrations on the same plugin method with ``plugins.registers_on``
* :feature:`617` Support ``inhibit_unhandled_exception_traceback``
* :feature:`635` ``slash run`` now supports ``--force-color``/``--no-color`` flags.
* :feature:`633` When using the `handling_exceptions`, it is now possible to obtain the exception object that was handled
* :feature:`-` Added ``SLASH_USER_SETTINGS=x`` environment variable to give a possibility to override the user slashrc file
* :feature:`592` Added ``exception_attributes`` dict to ``Error`` objects
* :feature:`600` Use `vintage` package for deprecations
* :feature:`595` Add `allowing_exceptions` context letting tests allow specific exceptions in selective context
* :bug:`606 major` Swallow python warnings during ast.parse
* :feature:`-` Added ``session.results.has_fatal_errors`` to check for fatal errors within a session
* :feature:`-` Slash now detects test functions being redefined, hiding previous tests, and warns about it
* :feature:`556` Long variable representations are now capped by default when distilling tracebacks
* :feature:`-` Assertions coming from plugins and modules loaded from the project's ``.slashrc`` now also have assertion rewriting introspection enabled
* :bug:`- major` Honor run.default_sources configuration when using slash list (thanks Pierre-Luc Tessier Gagné)
* :bug:`- major` Several Windows-specific fixes (thanks Pierre-Luc Tessier Gagné)
* :release:`1.2.5 <19-06-2017>`
* :bug:`-` Add exception_str shortcut for future compatibility on error objects
* :release:`1.2.4 <19-06-2017>`
* :bug:`581` Fix ``slash.exclude`` to work across fixture namespaces
* :bug:`580` ``tests_loaded`` hooks now get called with a list of tests including the interactive test if applicable
* :release:`1.2.2 <29-05-2017>`
* :bug:`564` Fix test collection bug causing tests to not be loaded with some plugins
* :release:`1.2.0 <30-04-2017>`
* :bug:`551 major` Fix stopping on error behavior when errors are reported on previous tests
* :feature:`529` Switch to PBR
* :feature:`508` Added optional ``end_message`` argument to ``notify_if_slow_context``, allowing better verbosity of long operations
* :bug:`490 major` Fixed behavior of plugin dependencies in cases involving mixed usage of plugin-level and hook-level dependencies
* :feature:`544` Added ``debug.debugger`` configuration to enable specifying preferred debugger. You can now pass ``-o debug.debugger=ipdb`` to prefer ipdb over pudb, for example
* :feature:`476` ``slash resume`` was greatly improved, and can now also fetch resumed tests from a recorded session in Backslash, if its plugin is configured
* :feature:`524` ``slash list``, ``slash list-config`` and ``slash list-plugins`` now supports ``--force-color``/``--no-color`` flags. The default changed from colored to colored only for tty
* :bug:`516 major` Fire test_interrupt earlier and properly mark session as interrupted when a test is interrupted
* :feature:`513` Add deep parametrization info (including nested fixtures) to the metadata variation info
* :feature:`512` ``slash list-config`` now receives a path filter for config paths to display
* :feature:`519` Add ``--no-output`` flag for ``slash list``
* :feature:`497` Major overhaul of CLI mechanics -- improve help message and usage, as well as cleaner error exits during the session configuration phase
* :feature:`467` Yield fixtures are now automatically detected by Slash -- using ``yield_fixture`` explicitly is no longer required
* :feature:`507` Test id can now be obtained via ``slash.context.test.id``
* :bug:`510 major` Explicitly fail fixtures which name is valid for tests (currently: ``test_`` prefix)
* :feature:`511` Support adding external logs ``Result.add_extra_log_path`` which will be retrieved by ``Result.get_log_paths()``
* :feature:`502` Added ``session_interrupt`` hook for when sessions are interrupted
* :release:`1.1.0 <22-11-2016>`
* :feature:`485` xunit plugin now saves the run results even when the session doesn't end gracefully (Thanks @eplaut)
* :feature:`369` Add ``slash.exclude`` to only skip specific parametrizations of a specific test or a dependent fixture. See `the cookbook section <http://slash.readthedocs.io/en/master/parameters.html#excluding-parameter-values>`_ for more details
* :bug:`483 major` Properly handle possible exceptions when examining traceback object attributes
* :feature:`484` ``slash list`` now indicates fixtures that are overriding outer fixtures (e.g. from ``slashconf.py``)
* :feature:`417` ``add_error``/``add_failure`` can now receive both message and exc_info information
* :feature:`359` Add trace logging of fixture values, including dependent fixtures
* :feature:`362` Add ability to intervene during test loading and change run order. This is done with a new ``tests_loaded`` hook and a new field in the test metadata controlling the sort order. See `the cookbook <http://slash.readthedocs.io/en/master/cookbook.html#controlling-test-execution-order>`_ for more details
* :feature:`352` Suite files can now contain filters on specific items via a comment beginning with ``filter:``, e.g. ``/path/to/test.py # filter: x and not y``
* :feature:`287` Add support for "facts" in test results, intended for coverage reports over relatively narrow sets of values (like OS, product configuration etc.)
* :feature:`195` Added ``this.test_start`` and ``this.test_end`` to enable fixture-specific test start and end hooks while they're active
* :feature:`384` Accumulate logs in the configuration phase of sessions and emit them to the session log. Until now this happened before logging gets configured so the logs would get lost
* :feature:`400` ``slash.skipped`` decorator is now implemented through the requirements mechanism. This saves a lot of time in unnecessary setup, and allows multiple skips to be assigned to a single test
* :feature:`462` Add ``log.errors_subpath`` to enable log files only recording added errors and failures.
* :feature:`403` add ``slash list-plugins`` to show available plugins and related information
* :feature:`461` ``yield_fixture`` now honors the ``scope`` argument
* :feature:`468` Slash now detects tests that accidentally contain ``yield`` statements and fails accordingly
* :bug:`479 major` When installing and activating plugins and activation fails due to incompatibility, the erroneous plugins are now automatically uninstalled
* :bug:`477 major` Fix assert_raises with message for un-raised exceptions
* :bug:`464 major` Fix exc_info leaks outside of ``assert_raises`` & ``handling_exceptions``
* :feature:`-` Added the ``entering_debugger`` hook to be called before actually entering a debugger
* :feature:`344` Exceptions recorded with ``handling_exceptions`` context now properly report the stack frames above the call
* :feature:`466` Add --relative-paths flag to ``slash list``
* :release:`1.0.2 <19-10-2016>`
* :bug:`481` Fixed tuple parameters for fixtures
* :release:`1.0.1 <07-08-2016>`
* :bug:`464` Fix reraising behavior from handling_exceptions
* :bug:`457` Fixed initialization order for *autouse* fixtures
* :release:`1.0.0 <26-06-2016>`
* :feature:`447` Added a more stable sorting logic for cartesian products of parametrizations
* :feature:`446` Exception tracebacks now include instance attributes to make debugging easier
* :feature:`397` Native Python warnings are now captured during testing sessions
* :feature:`407` Added ``--repeat-all`` option for repeating the entire suite several times
* :feature:`276` Added support for fixture aliases using ``slash.use``
* :feature:`439` Added support ``yield_fixture``
* :bug:`442 major` Prevent ``session_end`` from being called when ``session_start`` doesn't complete successfully
* :feature:`441` ``variation`` in test metadata now contains both ``id`` and ``values``. The former is a unique identification of the test variation, whereas the latter contains the actual fixture/parameter values when the test is run
* :feature:`401` session_end no longer called on plugins when session_start isn't called (e.g. due to errors with other plugins)
* :feature:`423` Added support for generator fixtures
* :feature:`437` Added ``test_avoided`` hook to be called when tests are completely skipped (e.g. requirements)
* :feature:`424` slash internal app context can now be instructed to avoid reporting to console (use ``report=False``)
* :feature:`436` ``slash list`` now fails by default if no tests are listed. This can be overriden by specifying ``--allow-empty``
* :feature:`435` Added ``swallow_types`` argument to exception_handling context to enable selective swallowing of specific exceptions
* :feature:`430` Added coverage plugin to generate code coverage report at the end of the run (``--with-coverage``)
* :feature:`428` Requirements using functions can now have these functions return tuples of (fullfilled, requirement_message) specifying the requirement message to display
* :feature:`427` Drop support for Python 2.6
* :feature:`416` Add --no-params for "slash list"
* :feature:`413` Test names inside files are now sorted
* :feature:`412` Add is_in_test_code to traceback json
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
