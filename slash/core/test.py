import functools
import itertools
from types import GeneratorType

from .._compat import iteritems, izip
from ..exception_handling import handling_exceptions
from ..exceptions import SkipTest, InvalidTest
from .fixtures.parameters import bound_parametrizations_context
from .runnable_test import RunnableTest
from .runnable_test_factory import RunnableTestFactory
from .requirements import get_requirements
from .tagging import get_tags
from .fixtures.utils import nofixtures

class TestTestFactory(RunnableTestFactory):

    def __init__(self, testclass):
        super(TestTestFactory, self).__init__(testclass)
        self.testclass = testclass

    def get_class_name(self):
        return self.testclass.__name__

    def _generate_tests(self, fixture_store):
        if is_abstract_base_class(self.testclass):
            return

        for test_method_name in dir(self.testclass):
            if not test_method_name.startswith("test"):
                continue

            for fixture_variation in self._iter_parametrization_variations(test_method_name, fixture_store):
                case = self.testclass(
                    test_method_name,
                    fixture_store=fixture_store,
                    fixture_namespace=fixture_store.get_current_namespace(),
                    variation=fixture_variation,
                )
                if self.testclass.__slash_skipped__:
                    case.run = functools.partial(SkipTest.throw, self.testclass.__slash_skipped_reason__)
                yield case  # pylint: disable=protected-access

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
    def __init__(self, test_method_name, fixture_store, fixture_namespace, variation):
        super(Test, self).__init__(fixture_store, fixture_namespace, variation)
        self._test_method_name = test_method_name

    def get_test_function(self):
        return getattr(self, self._test_method_name)

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
        method = self.get_test_function()
        return self._fixture_store.get_required_fixture_objects(method, namespace=self._fixture_namespace)

    def get_address_in_factory(self):
        returned = ''
        if self._test_method_name is not None:
            returned += ".{0}".format(self._test_method_name)
        return returned

    def _get_call_string(self, kwargs):
        if not kwargs:
            return ""
        return "({0})".format(", ".join("{0}={1!r}".format(k, v) for k, v in iteritems(kwargs)))

    def get_requirements(self):
        test_requirements = get_requirements(type(self)) + get_requirements(self.get_test_function())
        if nofixtures.is_marked(self.get_test_function()):
            return test_requirements
        return list(set(test_requirements + self._get_fixtures_requirements()))

    def run(self):  # pylint: disable=E0202
        """
        .. warning:: Not to be overriden
        """
        method = self.get_test_function()
        with bound_parametrizations_context(self._variation, self._fixture_store, self._fixture_namespace):
            _call_with_fixtures = functools.partial(self._fixture_store.call_with_fixtures, namespace=self._fixture_namespace)
            _call_with_fixtures(self.before, trigger_test_start=True)
            try:
                with handling_exceptions():
                    result = _call_with_fixtures(method, trigger_test_start=True)
                    if isinstance(result, GeneratorType):
                        raise InvalidTest('{} is a generator. Running generators is not supported'.format(method))

            finally:
                with handling_exceptions():
                    _call_with_fixtures(self.after, trigger_test_end=True)

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


def is_valid_test_name(name):
    return name.startswith('test_')
