The Slash Testing Framework
===========================

What is Slash?
--------------

Slash is a testing framework written in Python. Unlike many other testing frameworks out there, Slash focuses on building in-house testing solutions for large projects. It provides facilities and best practices for testing complete products, and not only unit tests for individual modules.

Slash provides several key features:
   
* A solid execution model based on fixtures, test factories and tests. This provides you with the flexibility you need to express your testing logic.
* Easy ways for extending the core functionality, adding more to the global execution environment and controlling how your tests interact with it.
* A rich configuration mechanism, helping you setting up your environment parameters and their various flavours.
* A plugin architecture, greatly simplifying adding extra functionality to your framework.

Diving in
---------

As a Test Author
~~~~~~~~~~~~~~~~

If you only want to write tests for running with Slash, you should head first to the :ref:`tour` section which should help you get started.

As a Framework Developer
~~~~~~~~~~~~~~~~~~~~~~~~

If you are looking to integrate Slash into your testing ecosystem, or want to learn how to extend its functionality and adapt it to specific purposes, head to the :ref:`customizing` section.

Table Of Contents
-----------------
       
.. toctree::
   :maxdepth: 2

   tour
   slash_run
   parameters
   tags
   fixtures
   errors
   customizing_slash
   configuration
   logging
   details
   hooks
   plugins
   builtin_plugins
   internals
   features
   advanced_usage
   cookbook
   faq
   api
   changelog
   development
   unit_testing
   



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

