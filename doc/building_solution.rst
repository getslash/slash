.. _building_solution:

Building a Testing Solution with Slash
==========================================

Slash is aimed at building complete testing solutions. In this section we will explain a basic way to accomplish this. We will be covering how to create a testing package containing tests and global state for those tests, as well as how to lay the entire solution out and create a basic runner entry point.

Let's say we're working in a company called *Microtech*, a company which manufactures microwaves. Let's also say we're now tasked with building the testing infrastructure for our microwave product line.

Creating a Package
------------------

The tests, as well as support code, will be implemented in a regular python package which we will be creating. We won't cover the theory or gory details of creating a Python package, but we'll show a simple example which covers it.

Our package name will be ``microtech_testing`` (the name plays no role in our solution, so you can choose whatever name you like). We will create a directory structure as follows::

  + src
     - setup.py
     + microtech_testing
         - __init__.py
       
A minimalistic ``setup.py`` would be:

.. code-block:: python

 from setuptools import setup, find_packages

 setup(name="microtech_testing",
      description="The testing solution for Microtech",
      version="1.0", 
      packages=find_packages(),
      install_requires=["slash"],
      )

.. note:: we require slash from this package. This is good because people will only have to install the ``microtech_testing`` package, and it will install Slash along with it as a dependency.

Creating the Tests
------------------

When building our in-house testing solution it is important to consider where to store the tests we are going to run. We can choose many different places, but two options make slightly more sense than others:

1. We can initializa a separate source repository for the tests (outside the testing package)
2. We can store them in a path inside the testing package

Since we are going to write utilities and helpers in our testing package to help our tests, it would be better to hold the tests inside ``michrotech_testing``. This way the tests are versioned alongside the utility code, and they can be both checked out at the same time conveniently.

We will create a path under the source root, calling it ``testsuite`` (although any other name will do as well)::

  + src
     - setup.py
     + microtech_testing
         - __init__.py
         + testsuite       # <--┬- added
             - __init__.py # <--┤
             - test_1.py   # <--┘

For now we will leave our test files empty. We'll get right back to them after setting up the environment in which they will run.

The Fixture
-----------

All of our tests will have to test a microwave device. In many cases this is called the *DUT*, or Device Under Test. Luckily for us, our company already has an SDK for accessing a microwave, and it published it as a Python package called ``microtech``.

However, our job isn't over. Since all tests need to access the object representing the microwave under test, this means we will have to initialize it somewhere, and make it accessible to all tests.

One approach for doing this is to add the initialization code to the ``before`` method of all tests involved, or even create a base class for all tests that does so. However, this is far from ideal, and has several downsides. 

Another possibility is to create a `test context <test_contexts>` and decorate all tests with it. This is slightly better, but here we'll explain how to do this using Slash's plugins and the global fixture it supports.

First, we will add the ``microtech`` package as a dependency of ``microtech_testing``. This makes sense, and will once again automatically install the SDK when the testing package is installed:

.. code-block:: python

 # setup.py
 ...
 setup(...
    #...
    install_requires=[
        "slash",
        "microtech", # <-- added
    ],
    #...
 )

Now we will use Slash's plugin mechanism, and create our customization plugin to do the work. We'll create the following under ``src/microtech_testing/slash_plugin.py``:

.. code-block:: python

  # src/microtech_testing/slash_plugin.py
  # microtech_site.py
  
  from slash import plugins
   
  class MicrotechTestingPlugin(plugins.PluginInterface):
      def get_name(self):
          return "microtech"

To initialize and make accessible a microwave instance, we'll use *the slash fixture global*. We already covered :ref:`the fixture global in brief in an earlier section <fixtures>`. We'll simply initialize and assign a microwave object at the beginning of the :ref:`session <sessions>`:

.. code-block:: python

 # src/microtech_testing/slash_plugin.py

 #...
 from microtech import Microwave
 from slash import fixture
 #...

 class MicrotechTestingPlugin(plugins.PluginInterface):
     # ...
     def session_start(self):
         fixture.microwave = Microwave("192.168.120.120")

.. note:: Yes. Our microwaves have IP addresses. Deal with it.

Creating the Runner
-------------------

We need a basic frontend to load and run our tests, as well as activate our plugin. Let's create it:

.. code-block:: python

 # src/microtech_testing/runner.py
 import slash
 import sys
 
 if __name__ == "__main__":
     with slash.get_application_context() as app:
         slash.run_tests(
             app.test_loader.iter_package("microtech_testing.testsuite")
         )
     sys.exit(0 if app.session.result.is_success() else -1)


The above skeleton takes care of most of the stuff you'd expect to see in a test runner (and in fact is very similar to ``slash run``). In order to make this play nicely with our plugin, we need to install and activate our plugin. This is how can achieve this:

.. code-block:: python

 # src/microtech_testing/runner.py
 ...
 from microtech_testing.slash_plugin import MicrotechTestingPlugin
 ...

 def customize_slash():
     slash.plugins.manager.install(MicrotechTestingPlugin(), activate=True)
     

 if __name__ == "__main__":
     customize_slash()
     with slash.get_application_context() as app:
     ...

We'll be using the ``customize_slash`` function for further enhancements in the next paragraphs.

Configuration and Parameters
----------------------------

In the previous example we hard-coded the microwave's address in our plugin. We would like, however, for each engineer running tests to specify his own microwave's address, most likely from the command line. 

Fortunately, Slash plugins can control the way command-line arguments are processed, with the ``configure_argument_parser`` and ``configure_from_parsed_args`` methods:

.. code-block:: python


 class MicrotechTestingPlugin(plugins.PluginInterface):
     # ...
     def configure_argument_parser(self, parser):
         parser.add_argument("-m", "--microwave-address", help="IP Address of microwave we are testing")
     def configure_from_parsed_args(self, args):
         self.microwave_address = args.microwave_address
     def start_session(self):
         fixture.microwave = Microwave(self.microwave_address)
     # ...

Let's say we also want to contain configurable parameters relevant to our tests -- for instance, microwave boot time in seconds. These can of course be hard-coded in our plugins, but are much better of as values in Slash's :ref:`configuration`. This way they can be changed from the outside world (e.g. with the -o flag).

This is very easy to do in our ``customize`` function:

.. code-block:: python
 
 # ...

 def customize_slash():
     # ...
     slash.config.extend({
         "microtech" : { 
             "microwave_boot_time_seconds" : 600,
         }
     })

.. note:: Yes. Our microwave takes 10 minutes to boot. Deal with it.

The ``extend`` method updates Slash's configuration with the given structure, allowing for the addition of the new paths. Now when we run our tests, we can, for instance, override the default value with ``-o microtech.microwave_boot_time_seconds=60000``.

Additional Hooks
----------------

Let's say we would like to automatically report all test exceptions to a centralized server in Microtech. All we have to do is just add an entry point in our plugin:

.. code-block:: python

 class MicrotechTestingPlugin(plugins.PluginInterface):
     # ...
     def exception_caught_before_debugger(self):
         requests.post(
            "http://bug_reports.microtech.com/report", 
            data={"microwave_id" : fixture.microwave.get_id()}
         )

For further reading, refer to the `hooks documentation <hooks>` to examine more ways you can use to customize the test running process.
