Changelog
=========

* :release `0.4.0 <15-12-2013>`
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
* :feature:`75` Support matching by parameters in FQN
* :feature:`75` Support running specific or partial tests via FQN
* :release:`0.0.2 <7-7-2013>`
* :feature:`46`: Added plugin.activate() to provide plugins with the ability to control what happens upon activation
* :feature:`40`: Added test context support - you can now decorate tests to provide externally implemented contexts for more flexible setups
* :feature:`-` Renamed slash.fixture to slash.g (fixture is an overloaded term that will maybe refer to test contexts down the road)
* :feature:`48`, #54: handle import errors and improve captured exceptions
* :feature:`3` Handle KeyboardInterrupts (quit fast), added the test_interrupt hook
* :feature:`5` add_critical_cleanup for adding cleanups that are always called (even on interruptions)


