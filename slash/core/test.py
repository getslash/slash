import functools
import inspect

from .._compat import iteritems
from ..exception_handling import handling_exceptions
from ..exceptions import SkipTest
from ..parameters import (iter_inherited_method_parameter_combinations,
                          iter_parameter_combinations,
                          set_parameter_values_context)
from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory


class TestTestFactory(RunnableTestFactory):

    def __init__(self, test, file_path, factory_name):
        super(TestTestFactory, self).__init__(file_path, factory_name)
        self.test = test

    def _generate_tests(self, fixture_store):
        if is_abstract_base_class(self.test):
            return

        for test_method_name in dir(self.test):
            if not test_method_name.startswith("test"):
                continue
            test_method = getattr(self.test, test_method_name)
            needed_fixtures = inspect.getargspec(test_method).args[1:]
            for before_kwargs in iter_inherited_method_parameter_combinations(self.test, 'before'):
                for test_kwargs in iter_parameter_combinations(test_method):
                    for after_kwargs in iter_inherited_method_parameter_combinations(self.test, 'after'):
                        for fixture_variation in fixture_store.iter_variations(needed_fixtures):
                            case = self.test(
                                test_method_name,
                                before_kwargs=before_kwargs,
                                test_kwargs=test_kwargs,
                                after_kwargs=after_kwargs,
                                needed_fixtures=needed_fixtures,
                                fixture_store=fixture_store,
                                fixture_namespace=fixture_store.get_current_namespace(),
                                fixture_variation=fixture_variation,
                            )
                            if self.test.__slash_skipped__:
                                case.run = functools.partial(SkipTest.throw, self.test.__slash_skipped_reason__)
                            yield case._get_address_in_factory(), case  # pylint: disable=protected-access



class Test(RunnableTest):
    """
    This is a base class for implementing unittest-style test classes.
    """
    def __init__(self, test_method_name, fixture_store, fixture_namespace, fixture_variation, needed_fixtures, before_kwargs=None, after_kwargs=None, test_kwargs=None):
        super(Test, self).__init__()
        self._test_method_name = test_method_name
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._fixture_variation = fixture_variation
        self._needed_fixtures = needed_fixtures
        self._before_kwargs = before_kwargs
        self._after_kwargs = after_kwargs
        self._test_kwargs = test_kwargs

    __slash_skipped__ = False
    __slash_skipped_reason__ = None
    __slash_needed_contexts__ = None


    @classmethod
    def skip_all(cls, reason=None):
        cls.__slash_skipped__ = True
        cls.__slash_skipped_reason__ = reason

    def _get_address_in_factory(self):
        returned = ''
        if self._before_kwargs or self._after_kwargs:
            returned += "{0}{1}".format(
                self._get_call_string(self._before_kwargs),
                self._get_call_string(self._after_kwargs),
            )
        if self._test_method_name is not None:
            returned += ".{0}".format(self._test_method_name)
            if self._test_kwargs:
                returned += self._get_call_string(self._test_kwargs)
        return returned

    def _get_call_string(self, kwargs):
        if not kwargs:
            return ""
        return "({0})".format(", ".join("{0}={1!r}".format(k, v) for k, v in iteritems(kwargs)))

    def run(self): # pylint: disable=E0202
        """_
        Not to be overriden
        """
        method = getattr(self, self._test_method_name)
        with set_parameter_values_context([self._before_kwargs, self._after_kwargs, self._test_kwargs]):
            self.before()
            try:
                with handling_exceptions():
                    fixture_kwargs = self._fixture_store.get_fixture_dict(
                        self._needed_fixtures,
                        namespace=self._fixture_namespace,
                        variation=self._fixture_variation)
                    method(**fixture_kwargs)  # pylint: disable=star-args
            finally:
                with handling_exceptions():
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
