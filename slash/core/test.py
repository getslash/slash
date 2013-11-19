import functools

from .._compat import iteritems
from ..utils import skip_test
from ..utils.fqn import ModuleTestAddress
from ..parameters import iterate_kwargs_options
from ..runnable_test import RunnableTest
from ..runnable_test_factory import RunnableTestFactory
from ..exception_handling import handling_exceptions

class Test(RunnableTest, RunnableTestFactory):
    """
    This is a base class for implementing unittest-style test classes.
    """
    def __init__(self, test_method_name, before_kwargs=None, after_kwargs=None, test_kwargs=None):
        super(Test, self).__init__()
        self._test_method_name = test_method_name
        self._before_kwargs = before_kwargs or {}
        self._after_kwargs = after_kwargs or {}
        self._test_kwargs = test_kwargs or {}

    __slash_skipped__ = False
    __slash_skipped_reason__ = None

    @classmethod
    def skip_all(cls, reason=None):
        cls.__slash_skipped__ = True
        cls.__slash_skipped_reason__ = reason

    @classmethod
    def _generate_tests(cls):
        if is_abstract_base_class(cls):
            return

        before_kwarg_sets = list(iterate_kwargs_options(cls.before))
        after_kwarg_sets = list(iterate_kwargs_options(cls.after))
        for test_method_name in dir(cls):
            if not test_method_name.startswith("test"):
                continue
            test_method = getattr(cls, test_method_name)
            for before_kwargs in before_kwarg_sets:
                for test_kwargs in iterate_kwargs_options(test_method):
                    for after_kwargs in after_kwarg_sets:
                        case = cls(
                            test_method_name,
                            before_kwargs=before_kwargs,
                            test_kwargs=test_kwargs,
                            after_kwargs=after_kwargs
                        )
                        if cls.__slash_skipped__:
                            case.run = functools.partial(
                                skip_test,
                                cls.__slash_skipped_reason__
                            )
                        yield case

    def run(self): # pylint: disable=E0202
        """
        Not to be overriden
        """
        method = getattr(self, self._test_method_name)
        self.before(**self._before_kwargs)
        try:
            with handling_exceptions():
                method(**self._test_kwargs)
        finally:
            with handling_exceptions():
                self.after(**self._after_kwargs)

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

    def get_address_in_module(self):
        return ModuleTestAddress(
            factory_name=type(self).__name__,
            method_name=self._test_method_name,
            method_kwargs=self._test_kwargs,
            before_kwargs=self._before_kwargs,
            after_kwargs=self._after_kwargs,
            )

    def _format_kwargs(self, kwargs):
        return ", ".join("{0}={1!r}".format(x, y) for x, y in iteritems(kwargs))

def abstract_test_class(cls):
    """
    Marks a class as **abstract**, thus meaning it is not to be run
    directly, but rather via a subclass.
    """
    assert issubclass(cls, Test), "abstract_test_class only operates on slash.Test subclasses"
    cls.__slash_abstract__ = True
    return cls

def is_abstract_base_class(cls):
    """
    Checks if a given class is abstract.

    .. seealso:: :func:`abstract_test_class`
    """
    return bool(cls.__dict__.get("__slash_abstract__", False))
