Exceptions
==========

Exceptions are an important part of the testing workflow. They happen all the time -- whether they indicate a test lifetime event or an actual error condition. Exceptions need to be debugged, handled, responded to, and sometimes with delicate logic of what to do when.

As explained in the :ref:`quickstart` section, you can enter a debugger when exceptions occur via the ``--pdb`` flag. Shakedown will attempt to invoke ``pudb`` or ``ipdb`` if you have them installed, but will revert to the default ``pdb`` if they are not present.

Exception Handling Context
--------------------------

Shakedown contains a special context, :func:`shakedown.handling_exceptions`. The purpose of this context is to give your infrastructure a chance to handle an erroneous case as close as possible to its occurrence. 

This context can be safely nested -- once an exception is handled, it is appropriately marked, so the outer contexts will skip handling it::

    from shakedown import handling_exceptions

    def some_function():
        with handling_exceptions():
            do_something_that_might_fail()

    with handling_exceptions():
        some_function()

.. autofunction:: shakedown.exception_handling.handling_exceptions

Exception Marks
---------------

The exception handling context relies on a convenience mechanism for marking exceptions. 

.. autofunction:: shakedown.exception_handling.is_exception_marked
.. autofunction:: shakedown.exception_handling.mark_exception
.. autofunction:: shakedown.exception_handling.get_exception_mark


Marks with Special Meanings
---------------------------

TODO
