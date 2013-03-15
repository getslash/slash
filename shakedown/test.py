from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory

class Test(RunnableTest, RunnableTestFactory):
    """
    This is a base class for implementing unittest-style test classes.
    """
    def __init__(self, test_method_name):
        super(Test, self).__init__()
        self._test_method_name = test_method_name
    @classmethod
    def generate_tests(cls):
        if is_abstract_base_class(cls):
            return []
        return [cls(test_method_name)
                for test_method_name in dir(cls)
                if test_method_name.startswith("test")]
    def run(self):
        """
        Not to be overriden
        """
        method = getattr(self, self._test_method_name)
        self.before()
        try:
            method()
        finally:
            self.after()
    def before(self):
        """
        Gets called before each separate case generated from this test class
        """
        pass
    def after(self):
        """
        Gets called after each separate case from this test class executed, assuming :meth:`before` was successful.
        """
        pass
    def get_canonical_name(self):
        return "{0}:{1}".format(super(Test, self).get_canonical_name(), self._test_method_name)


def abstract_test_class(cls):
    """
    Marks a class as **abstract**, thus meaning it is not to be run
    directly, but rather via a subclass.
    """
    assert issubclass(cls, Test), "abstract_test_class only operates on shakedown.Test subclasses"
    cls.__shakedown_abstract__ = True
    return cls

def is_abstract_base_class(cls):
    """
    Checks if a given class is abstract.

    .. seealso:: :func:`abstract_test_class`
    """
    return bool(cls.__dict__.get("__shakedown_abstract__", False))
