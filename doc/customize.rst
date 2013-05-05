.. _customize:

Customization
=============

Shakedown's can be customized for various projects and workflows pretty easily. It can change from "generic testing framework" to "the testing framework for X" in a matter of a few lines of code, and without any changes to Shakedown's code itself. In this section we will explain how to do this, with a fictitious example.

Let's say we're working in a company called *Microtech*, a company which manufactures microwaves. Let's also say we're now tasked with building the testing infrastructure for our microwave product line.

First Steps
-----------

The simplest way to tailor Shakedown to our needs is by implementing an *adapter package*. This is a regular (installable) python package which, when installed, customizes Shakedown to our needs. We won't cover the theory or gory details of creating a Python package, but we'll show a simple example which covers it.

Our package name will be ``microtech_testing`` (the name plays no role in our integration, so you can choose whatever name you like). We will create a directory structure as follows::

  + src
     - setup.py
     + microtech_testing
         - __init__.py
       
A minimalistic ``setup.py`` would be:

.. code-block:: python

 from setuptools import setup, find_packages

 setup(name="microtech_testing",
      description="An adapter layer for shakedown, to test ",
      version="1.0", 
      packages=find_packages(exclude=["tests"]),
      install_requires=["shakedown"],
      )

.. note:: we require shakedown from this package. This is good because people will only have to install the ``microtech_testing`` package, and it will install Shakedown along with it as a dependency.

The main entry point for the customization is a function we are going to implement. Let's call it ``customize_shakedown``, and we'll put it in ``__init__.py``:

.. code-block:: python
 
 # microtech_testing/__init__.py

 def customize_shakedown():
     pass

To let shakedown load our customization on startup, we'll use a feature of ``setuptools`` called *entry points*. This lets us register specific functions in "slots", to be read by other packages. We'll append the following to our ``setup.py`` file:

.. code-block:: python

 # setup.py
 
 ...
 setup(...
    # ...
    entry_points = {
        "shakedown.site.customize": [
            "microtech_testing_customize = microtech_testing:customize_shakedown"
            ]
        },
    # ...
 )

.. note:: the ``microwave_testing_customize`` above is an arbitrary name. It only serves as an identification for your customization entry point. 
.. note:: You can read more about setuptools entry points `here <http://stackoverflow.com/questions/774824/explain-python-entry-points>`_.

Now Shakedown will call our customize function when loading. Now it's time to add actual customization to our package. 


The Fixture
-----------

All of our tests will have to test a microwave device. In many cases this is called the *DUT*, or Device Under Test. Luckily for us, our company already has an SDK for accessing a microwave, and it published it as a Python package called ``microtech``.

However, our job isn't over. Since all tests need to access the object representing the microwave under test, this means we will have to initialize it somewhere, and make it accessible to all tests.

One approach for doing this is to add the initialization code to the ``before`` method of all tests involved, or even create a base class for all tests that does so. However, this is far from ideal, and has several downsides. The Shakedown approach to solving this is by using a mix of *plugins and fixtures*, as described below.

First, we will add the ``microtech`` package as a dependency of ``microtech_testing``. This makes sense, and will once again automatically install the SDK when the testing package is installed:

.. code-block:: python

 # setup.py
 ...
 setup(...
    #...
    install_requires=[
        "shakedown",
        "microtech", # <-- added
    ],
    #...
 )

Now we will use Shakedown's plugin mechanism, and create our customization plugin to do the work. We'll create the following under ``src/microtech_testing/shakedown_plugin.py``:

.. code-block:: python

  # src/microtech_testing/shakedown_plugin.py
  # microtech_site.py
  
  from shakedown import plugins
   
  class MicrotechTestingPlugin(plugins.PluginInterface):
      def get_name(self):
          return "microtech"

We also want to install and activate it by default, so we'll add this to our customize function:

.. code-block:: python

 # microtech_testing/__init__.py
 import shakedown
 from .shakedown_plugin iport MicrotechTestingPlugin

 def customize_shakedown():
     shakedown.plugins.manager.install(MicrotechTestingPlugin(), activate=True)

Now each run of shakedown will automatically load and activate our plugin.

To initialize and make accessible a microwave instance, we'll use *the shakedown fixture global*. We already covered :ref:`the fixture global in brief in an earlier section <fixtures>`. We'll simply initialize and assign a microwave object at the beginning of the :ref:`session <sessions>`:

.. code-block:: python

 # src/microtech_testing/shakedown_plugin.py

 #...
 from microtech import Microwave
 from shakedown import fixture
 #...

 class MicrotechTestingPlugin(plugins.PluginInterface):
     # ...
     def session_start(self):
         fixture.microwave = Microwave("192.168.120.120")

.. note:: Yes. Our microwaves have IP addresses. Deal with it.

Configuration and Parameters
----------------------------

In the previous example we hard-coded the microwave's address in our plugin. We would like, however, for each engineer running tests to specify his own microwave's address, most likely from the command line. 

Fortunately, Shakedown plugins can control the way command-line arguments are processed, with the ``configure_argument_parser`` and ``configure_from_parsed_args`` methods:

.. code-block:: python

 # src/microtech_testing/shakedown_plugin.py
 #...

 class MicrotechTestingPlugin(plugins.PluginInterface):
     # ...
     def configure_argument_parser(self, parser):
         parser.add_argument("-m", "--microwave-address", help="IP Address of microwave we are testing")
     def configure_from_parsed_args(self, args):
         self.microwave_address = args.microwave_address
     def start_session(self):
         fixture.microwave = Microwave(self.microwave_address)
     # ...

Let's say we also want to contain configurable parameters relevant to our tests -- for instance, microwave boot time in seconds. These can of course be hard-coded in our plugins, but are much better of as values in Shakedown's :ref:`configuration`. This way they can be changed from the outside world (e.g. with the -o flag).

This is very easy to do in our ``customize`` function:

.. code-block:: python
 
 # microtech_testing/__init__.py
 # ...

 def customize_shakedown():
     # ...
     shakedown.config.extend({
         "microtech" : { 
             "microwave_boot_time_seconds" : 600,
         }
     })

.. note:: Yes. Our microwave takes 10 minutes to boot. Deal with it.

The ``extend`` method updates Shakedown's configuration with the given structure, allowing for the addition of the new paths. Now when we run our tests, we can, for instance, override the default value with ``-o microtech.microwave_boot_time_seconds=60000``.

Additional Hooks
----------------

Let's say we would like to automatically report all test exceptions to a centralized server in Microtech. All we have to do is just add an entry point in our plugin:

.. code-block:: python

 # src/microtech_testing/shakedown_plugin.py
 #...

 class MicrotechTestingPlugin(plugins.PluginInterface):
     # ...
     def exception_caught_before_debugger(self):
         requests.post(
            "http://bug_reports.microtech.com/report", 
            data={"microwave_id" : fixture.microwave.get_id()}
         )

For further reading, refer to the `hooks documentation <hooks>` to examine more ways you can use to customize the test running process.

Notes About Packaging
---------------------

When using the above customization method, once the ``microtech_testing`` package is installed, shakedown will *always* load it when starting up. This means that if you would like to have several different customizations of Shakedown, it will have to be in separate **virtualenvs**, or separate Python installations.

On the upside, this means that you can have several customization packages working together. For instance, if Microtech were to expand to another product line, say coffee machines, you can have two separate specific packages and one generic. Namely, ``microtech_microwave_testing`` will set up microwave testing fixtures and ``microtech_coffee_testing`` will set up coffee machine testing fixtures. Both can depend on a single common package (``microtech_testing`` for instance) which will only supply the generic facilities for testing any product that's produced by Microtech.

Other Customization Options
---------------------------

In addition to entry points, Shakedown looks for other locations to load code on startup. These can sometimes be used for customization as well.

**shakerc file**
  If the file ``~/.shakedown/shakerc`` exists, it is loaded and executed as a regular Python file by Shakedown on startup.

**SHAKEDOWN_SETTINGS**
  If an environment variable named ``SHAKEDOWN_SETTINGS`` exists, it is assumed to point at a file path or URL to laod as a regular Python file on startup.


