Customization
=============

While a lot of effort was put into making shakedown very generic and not taylored to any specific product being tested, in many cases it is desired to customize it to a specific use case.

We will demonstrate the customization process via a fictional case study.

Fictional Case Study - Testing Microwaves
-----------------------------------------

Let's assume we are now working in a microwave company, *microtech*, and we would like to test microwaves. In such cases we will have several things we want to tweak:

1. We would like to receive some information about the microwave being tested, possibly from command line
2. We would like to use a pre-written module that abstracts a microwave, implemented as ``microtech.microwave.Microwave``.
3. We would like to add update malfunctions test to a manufacturing-related web service which is specific to our company, at ``http://mfg.microtech.com/notify_malfunction``

Writing the Site File
---------------------

The **site file** is a Python source file that when executed, customizes shakedown to your needs. We'll start by writing a plugin that will enable us to initialize a microwave object at the beginning of each test:

.. code-block:: python

  # microtech_site.py
  
  from microtech.microwave import Microwave

  from shakedown import fixture
  from shakedown import plugins
   
  class MicrotechTesting(plugins.PluginInterface):
      def get_name(self):
          return "microtech"
      def configure_argument_parser(self, parser):
          parser.add_argument("-m", "--microwave-id", help="Microwave we are testing")
      def configure_from_parsed_args(self, args):
          fixture.microwave = Microwave(args.microwave_id)
  plugins.manager.install(MicrotechTesting(), activate=True)


In the above snippet we define, install and activate a plugin that will initialize microwave objects when running shakedown. For more information about how we do this you can also refer to :ref:`the relevant section about plugins <plugins>`.

The fact that we're using a plugin gives us a lot of freedom. For instance, we can turn a microwave off and on again at the end of each test:

.. code-block:: python

  # ... class MicrotechTesting(...) contd.
      def end_test(self):
          fixture.microwave.turn_off()
	  fixture.microwave.turn_on()

We can also implement our third requirement as a part of the plugin:

.. code-block:: python

  # ... class MicrotechTesting(...) contd.
      def exception_caught_before_debugger(self):
          requests.post(
             "http://mfg.microtech.com/notify_malfunction", 
             data={"microwave_id" : fixture.microwave.get_id()}
          )
       
Site files can also elegantly extend the configuration structure:

.. code-block:: python

  shakedown.config.extend({
      "manufacturing" : {
          "notify_url" : "http://mfg.microtech.com/notify_malfunction", 
      }
  })

You can also defer or add loading to specific external sources, like URLs or files:

 import shakedown.site
 shakedown.site.load("http://company.server.com/shakedown_customization.py")

Loading the Site File
---------------------

Shakedown looks for several places to load custom site files:

1. A file named ``~/.shakedown/shakerc`` will be loaded, if found
2. An environment variable, SHAKEDOWN_SETTINGS=..., which points at either a URL or a file to load

.. autofunction:: shakedown.site.load

