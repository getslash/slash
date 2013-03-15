The ``shakedown.Test`` Class
============================

The ``shakedown.Test`` class is a fusion between :class:`.RunnableTest` and :class:`.RunnableTestFactory`, where the generated tests are customized constructions of the test itself.

The Basics
----------

*TODO*

Abstract Base Tests
-------------------

Sometimes you want tests that won't be executed on their own, but rather function as bases to derived tests::

    class FileTestBase(Test):
        def test_has_write_method(self):
            assert_true(hasattr(self.file, "write"))
        def test_has_read_method(self):
            assert_true(hasattr(self.file, "read"))
    
    class RegularFileTest(FileTestBase):
        def before(self):
            super(RegularFileTest, self).before()
            self.file = open("somefile", "wb")
    
    class SocketFileTest(FileTestBase):
        def before(self):
            super(SocketFileTest, self).before()
            self.file = connect_to_some_server().makefile()

If you try running the above code via Shakedown, it will fail. This is because Shakedown tries to run all cases in ``FileTestBase``, which cannot run due to the lack of a ``before()`` method.

This is solved with the :func:`shakedown.abstract_test_class` decorator::
    
    @shakedown.abstract_test_class
    class FileTestBase(Test):
        def test_has_write_method(self):
            assert_true(hasattr(self.file, "write"))
        def test_has_read_method(self):
            assert_true(hasattr(self.file, "read"))

.. autofunction:: shakedown.abstract_test_class
