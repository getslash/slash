import functools
import itertools

from .._compat import iteritems
from ..exception_handling import handling_exceptions
from ..exceptions import SkipTest
from ..utils.python import getargspec
from .fixtures.parameters import bound_parametrizations_context, get_parametrization_fixtures
from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory


class TestTestFactory(RunnableTestFactory):

    def __init__(self, test, file_path, factory_name, module_name):
        super(TestTestFactory, self).__init__(file_path=file_path, factory_name=factory_name, module_name=module_name)
        self.test = test

    def _generate_tests(self, fixture_store):
        if is_abstract_base_class(self.test):
            return

        for test_method_name in dir(self.test):
            if not test_method_name.startswith("test"):
                continue

            test_method = getattr(self.test, test_method_name)
            needed_fixtures = self._get_needed_fixtures(test_method)

            for param_variation in self._iter_parametrization_variations(test_method_name, fixture_store):
                case = self.test(
                    test_method_name,
                    needed_fixtures=needed_fixtures,
                    fixture_store=fixture_store,
                    fixture_namespace=fixture_store.get_current_namespace(),
                    param_variation=param_variation,
                )
                if self.test.__slash_skipped__:
                    case.run = functools.partial(SkipTest.throw, self.test.__slash_skipped_reason__)
                yield case._get_address_in_factory(), case  # pylint: disable=protected-access

    def _get_needed_fixtures(self, method):
        parametrized = set(p.name for p in get_parametrization_fixtures(method))
        return [name for name in getargspec(method).args[1:] if name not in parametrized]

    def _iter_parametrization_variations(self, test_method_name, fixture_store):
        return fixture_store.iter_parameterization_variations(methods=itertools.chain(
            self._get_all_before_methods(),
            [getattr(self.test, test_method_name)],
            self._get_all_after_methods()))

    def _get_all_before_methods(self):
        return self._iter_inherited_methods('before')

    def _get_all_after_methods(self):
        return self._iter_inherited_methods('after')

    def _iter_inherited_methods(self, name):

        for cls in self.test.__mro__:
            if hasattr(cls, name):
                yield getattr(cls, name)


class Test(RunnableTest):
    """
    This is a base class for implementing unittest-style test classes.
    """
    def __init__(self, test_method_name, fixture_store, fixture_namespace, param_variation, needed_fixtures):
        super(Test, self).__init__()
        self._test_method_name = test_method_name
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._param_variation = param_variation
        self._needed_fixtures = needed_fixtures

    __slash_skipped__ = False
    __slash_skipped_reason__ = None
    __slash_needed_contexts__ = None


    @classmethod
    def skip_all(cls, reason=None):
        cls.__slash_skipped__ = True
        cls.__slash_skipped_reason__ = reason

    def _get_address_in_factory(self):
        returned = ''
        if self._test_method_name is not None:
            returned += ".{0}".format(self._test_method_name)
        return returned

    def _get_call_string(self, kwargs):
        if not kwargs:
            return ""
        return "({0})".format(", ".join("{0}={1!r}".format(k, v) for k, v in iteritems(kwargs)))

    def run(self):  # pylint: disable=E0202
        """_
        Not to be overriden
        """
        method = getattr(self, self._test_method_name)
        with bound_parametrizations_context(self._param_variation):
            self.before()
            try:
                with handling_exceptions():
                    fixture_kwargs = self._fixture_store.get_fixture_dict(
                        self._needed_fixtures,
                        namespace=self._fixture_namespace)
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
