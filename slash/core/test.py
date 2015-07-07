import functools
import itertools

from .._compat import iteritems, izip, xrange
from ..exception_handling import handling_exceptions
from ..exceptions import SkipTest
from .fixtures.parameters import bound_parametrizations_context
from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory
from .requirements import get_requirements
from .tagging import get_tags


class TestTestFactory(RunnableTestFactory):

    def __init__(self, testclass):
        super(TestTestFactory, self).__init__(testclass)
        self.testclass = testclass

    def _generate_tests(self, fixture_store):
        if is_abstract_base_class(self.testclass):
            return

        for test_method_name in dir(self.testclass):
            if not test_method_name.startswith("test"):
                continue

            for fixture_variation in self._iter_parametrization_variations(test_method_name, fixture_store):
                for _ in xrange(self._get_num_repetitions(getattr(self.testclass, test_method_name))):
                    case = self.testclass(
                        test_method_name,
                        fixture_store=fixture_store,
                        fixture_namespace=fixture_store.get_current_namespace(),
                        fixture_variation=fixture_variation,
                    )
                    if self.testclass.__slash_skipped__:
                        case.run = functools.partial(SkipTest.throw, self.testclass.__slash_skipped_reason__)
                    yield case._get_address_in_factory(), case  # pylint: disable=protected-access

    def _iter_parametrization_variations(self, test_method_name, fixture_store):
        return fixture_store.iter_parametrization_variations(methods=itertools.chain(
            izip(itertools.repeat('before'), self._get_all_before_methods()),
            izip(itertools.repeat('after'), self._get_all_after_methods()),
            [getattr(self.testclass, test_method_name)],
        ))

    def _get_all_before_methods(self):
        return self._iter_inherited_methods('before')

    def _get_all_after_methods(self):
        return self._iter_inherited_methods('after')

    def _iter_inherited_methods(self, name):

        for cls in self.testclass.__mro__:
            if hasattr(cls, name):
                yield getattr(cls, name)

    def get_unmet_requirements(self):
        raise NotImplementedError() # pragma: no cover


class Test(RunnableTest):
    """
    This is a base class for implementing unittest-style test classes.
    """
    def __init__(self, test_method_name, fixture_store, fixture_namespace, fixture_variation):
        super(Test, self).__init__()
        self._test_method_name = test_method_name
        self._fixture_store = fixture_store
        self._fixture_namespace = fixture_namespace
        self._fixture_variation = fixture_variation

    def get_tags(self):
        return get_tags(type(self)) + get_tags(getattr(type(self), self._test_method_name))

    __slash_skipped__ = False
    __slash_skipped_reason__ = None
    __slash_needed_contexts__ = None


    @classmethod
    def skip_all(cls, reason=None):
        cls.__slash_skipped__ = True
        cls.__slash_skipped_reason__ = reason

    def get_required_fixture_objects(self):
        method = getattr(self, self._test_method_name)
        return self._fixture_store.get_required_fixture_objects(method, namespace=self._fixture_namespace, is_method=True)

    def _get_address_in_factory(self):
        returned = ''
        if self._test_method_name is not None:
            returned += ".{0}".format(self._test_method_name)
        if self._fixture_variation:
            returned += '({0})'.format(self._fixture_variation.representation)
        return returned

    def _get_call_string(self, kwargs):
        if not kwargs:
            return ""
        return "({0})".format(", ".join("{0}={1!r}".format(k, v) for k, v in iteritems(kwargs)))

    def get_requirements(self):
        return get_requirements(type(self)) + get_requirements(getattr(self, self._test_method_name))

    def run(self):  # pylint: disable=E0202
        """
        .. warning:: Not to be overriden
        """
        method = getattr(self, self._test_method_name)
        with bound_parametrizations_context(self._fixture_variation):
            self._fixture_store.activate_autouse_fixtures_in_namespace(self._fixture_namespace)
            self.before()
            try:
                with handling_exceptions():
                    self._fixture_store.call_with_fixtures(
                        method, namespace=self._fixture_namespace,
                        is_method=True,
                    )
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
        Gets called after each separate case from this test class executed, assuming :meth:`.before` was successful.
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
