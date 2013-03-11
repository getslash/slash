Quick Start
===========

In this tutorial we will be covering the basics of using Shakedown to write and run tests. 

The Test Class
--------------

For anyone familiar with ``unittest``'s interface, the easiest way to get started is with the ``shakedown.Test`` base class::

    import shakedown

    class MyTest(shakedown.Test):
        def test_something(self):
            pass # <-- test logic here!

We can save this as a Python file, for instance as ``my_test.py``. Then we can run it using the ``shake run`` command::

    $ shake run my_test.py

Cleanups
--------

**STUB**
