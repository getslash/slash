import itertools
import traceback
import os
from types import FunctionType, GeneratorType
from contextlib import contextmanager

from emport import import_file
from logbook import Logger

import dessert
import sys

from .conf import config
from ._compat import iteritems, string_types
from .ctx import context
from .core.local_config import LocalConfig
from .core.runnable_test import RunnableTest
from .core.test import Test, TestTestFactory
from .core.function_test import FunctionTestFactory
from .exception_handling import handling_exceptions
from .exceptions import CannotLoadTests
from .core.runnable_test_factory import RunnableTestFactory
from .utils import add_error
from .utils.pattern_matching import Matcher

_logger = Logger(__name__)


class Loader(object):

    """
    Provides iteration interfaces to load runnable tests from various places
    """

    def __init__(self):
        super(Loader, self).__init__()
        if config.root.run.filter_string:
            self._matcher = Matcher(config.root.run.filter_string)
        else:
            self._matcher = None
        self._local_config = LocalConfig()

    def get_runnables(self, paths, sort_key=None):
        assert context.session is not None
        returned = self._collect(self._get_iterator(paths))
        if sort_key is not None:
            returned.sort(key=sort_key)
        return returned

    def _collect(self, iterator):
        returned = []
        context.reporter.report_collection_start()
        try:
            for x in iterator:
                returned.append(x)
                context.reporter.report_test_collected(returned, x)
        finally:
            context.reporter.report_collection_end(returned)
        context.session.increment_total_num_tests(len(returned))
        return returned

    def _get_iterator(self, thing):
        if isinstance(thing, (list, GeneratorType, itertools.chain)):
            return itertools.chain.from_iterable(self._get_iterator(x) for x in thing)
        if isinstance(thing, string_types):
            return self._iter_test_address(thing)
        if isinstance(thing, RunnableTest):
            return [thing]

        if not isinstance(thing, RunnableTestFactory):
            thing = self._get_runnable_test_factory(thing)

        return thing.generate_tests(fixture_store=context.session.fixture_store)

    def _iter_test_address(self, address):
        if ':' in address:
            path, address_in_file = address.split(':', 1)
        else:
            path = address
            address_in_file = None

        for test in self._iter_path(path):
            if address_in_file is not None:
                if not self._address_in_file_matches(address_in_file, test):
                    continue
            yield test

    def _address_in_file_matches(self, address_in_file, test):
        if address_in_file == test.__slash__.factory_name:
            return True
        test_address_in_file = test.__slash__.address_in_file
        if address_in_file == test_address_in_file:
            return True
        if '(' in test_address_in_file:
            if address_in_file == test_address_in_file[:test_address_in_file.index('(')]:
                return True

        return False

    def _iter_path(self, path):
        return self._iter_paths([path])

    def _iter_paths(self, paths):
        paths = list(paths)
        for path in paths:
            if not os.path.exists(path):
                msg = "Path {0} could not be found".format(path)
                add_error(msg)
                raise CannotLoadTests(msg)
        for path in paths:
            for file_path in _walk(path):
                _logger.debug("Checking {0}", file_path)
                if not self._is_file_wanted(file_path):
                    _logger.debug("{0} is not wanted. Skipping...", file_path)
                    continue
                module = None
                try:
                    with handling_exceptions(context="during import"):
                        with dessert.rewrite_assertions_context():
                            module = import_file(file_path)
                except Exception as e:
                    tb_file, tb_lineno, _, _ = traceback.extract_tb(sys.exc_info()[2])[-1]
                    raise CannotLoadTests(
                        "Could not load {0!r} ({1}:{2} - {3})".format(file_path, tb_file, tb_lineno, e))
                if module is not None:
                    with self._adding_local_fixtures(file_path, module):
                        for runnable in self._iter_runnable_tests_in_module(file_path, module):
                            if self._is_excluded(runnable):
                                continue
                            yield runnable

    @contextmanager
    def _adding_local_fixtures(self, file_path, module):
        context.session.fixture_store.push_namespace()
        try:
            self._local_config.push_path(os.path.dirname(file_path))
            try:
                context.session.fixture_store.add_fixtures_from_dict(
                    self._local_config.get_dict())
                context.session.fixture_store.add_fixtures_from_dict(
                    vars(module))
                context.session.fixture_store.resolve()
                yield
            finally:
                self._local_config.pop_path()
        finally:
            context.session.fixture_store.pop_namespace()

    def _is_excluded(self, test):
        if self._matcher is None:
            return False
        return not self._matcher.matches(test.__slash__)

    def _is_file_wanted(self, filename):
        return filename.endswith(".py")

    def _iter_runnable_tests_in_module(self, file_path, module):
        for thing_name, thing in iteritems(vars(module)):
            if thing is RunnableTestFactory:  # probably imported directly
                continue

            factory = self._get_runnable_test_factory(thing)

            if factory is None:
                continue

            factory.set_factory_name(thing_name)
            factory.set_module_name(module.__name__)
            factory.set_filename(file_path)

            for test in factory.generate_tests(fixture_store=context.session.fixture_store):
                assert test.__slash__ is not None
                yield test

    def _get_runnable_test_factory(self, thing):

        if isinstance(thing, type) and issubclass(thing, Test):
            return TestTestFactory(thing)

        if isinstance(thing, FunctionType):
            if thing.__name__.startswith('test_'):
                return FunctionTestFactory(thing)

        return None


def _walk(p):
    if os.path.isfile(p):
        return [p]
    return (os.path.join(dirname, filename)
            for dirname, _, filenames in os.walk(p)
            for filename in filenames)
