import itertools
import os
from types import FunctionType, GeneratorType
from contextlib import contextmanager

from emport import import_file
from logbook import Logger

import dessert

from .conf import config
from ._compat import iteritems, string_types
from .ctx import context
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

    def get_runnables(self, paths, sort_key=None):
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

        return returned

    def _get_iterator(self, thing):
        if isinstance(thing, (list, GeneratorType, itertools.chain)):
            return itertools.chain.from_iterable(self._get_iterator(x) for x in thing)
        if isinstance(thing, string_types):
            return self._iter_test_address(thing)
        if isinstance(thing, RunnableTest):
            return [thing]

        factory = self._get_runnable_test_factory(thing)
        if factory is None:
            raise ValueError("Cannot get runnable tests from {0!r}".format(thing))

        return factory.generate_tests()

    def _iter_test_address(self, address):
        if ':' in address:
            path, address_in_file = address.split(':', 1)
        else:
            path = address
            address_in_file = None

        for test in self._iter_path(path):
            if address_in_file is not None:
                if address_in_file not in (test.__slash__.factory_name, test.__slash__.address_in_file):
                    continue
            yield test

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
                with self._handling_import_errors(file_path):
                    try:
                        with dessert.rewrite_assertions_context():
                            module = import_file(file_path)
                    except Exception as e:
                        raise CannotLoadTests("Could not load {0!r} ({1})".format(file_path, e))
                if module is not None:
                    for runnable in self._iter_runnable_tests_in_module(file_path, module):
                        if self._is_excluded(runnable):
                            continue
                        yield runnable

    @contextmanager
    def _handling_import_errors(self, file_path):
        with handling_exceptions(context="during import", swallow=(context.session is not None)):
            try:
                yield
            except Exception as e:
                _logger.error("Failed to import {0} ({1})", file_path, e)
                raise

    def _is_excluded(self, test):
        if self._matcher is None:
            return False
        return not self._matcher.matches(test.__slash__.address)

    def _is_file_wanted(self, filename):
        return filename.endswith(".py")

    def _iter_runnable_tests_in_module(self, file_path, module):
        for thing_name, thing in iteritems(vars(module)):
            if thing is RunnableTestFactory: # probably imported directly
                continue

            factory = self._get_runnable_test_factory(thing, file_path, thing_name)
            if factory is None:
                continue

            for test in factory.generate_tests():
                assert test.__slash__ is not None
                yield test

    def _get_runnable_test_factory(self, thing, file_path='', name=''):
        if isinstance(thing, type) and issubclass(thing, Test):
            return TestTestFactory(thing, file_path, name)

        if isinstance(thing, FunctionType) and name.startswith('test_'):
            return FunctionTestFactory(func=thing, file_path=file_path, factory_name=name)

        return None

def _walk(p):
    if os.path.isfile(p):
        return [p]
    return (os.path.join(dirname, filename)
            for dirname, _, filenames in os.walk(p)
            for filename in filenames)
