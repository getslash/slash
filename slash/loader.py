import itertools
import traceback
import os
import sys
from types import FunctionType, GeneratorType
from contextlib import contextmanager

import dessert
from emport import import_file
from logbook import Logger
from sentinels import NOTHING


from .conf import config
from ._compat import string_types
from .ctx import context
from .core.local_config import LocalConfig
from .core.markers import repeat_marker
from . import hooks
from .core.runnable_test import RunnableTest
from .core.test import Test, TestTestFactory, is_valid_test_name
from .core.function_test import FunctionTestFactory
from .exception_handling import handling_exceptions, mark_exception_handled, get_exception_frame_correction
from .exceptions import CannotLoadTests
from .core.runnable_test_factory import RunnableTestFactory
from .utils.pattern_matching import Matcher
from .utils.python import check_duplicate_functions
from .resuming import ResumedTestData
from .utils.interactive import generate_interactive_test

_logger = Logger(__name__)


class Loader(object):

    """
    Provides iteration interfaces to load runnable tests from various places
    """

    def __init__(self):
        super(Loader, self).__init__()
        self._local_config = LocalConfig()
        self._duplicate_funcs = set()

    _cached_matchers = NOTHING

    def _get_matchers(self):
        if self._cached_matchers is NOTHING:
            if config.root.run.filter_strings:
                self._cached_matchers = [Matcher(s) for s in config.root.run.filter_strings]
            else:
                self._cached_matchers = None
        return self._cached_matchers


    def get_runnables(self, paths, prepend_interactive=False):
        assert context.session is not None
        sources = self._generate_repeats(self._generate_test_sources(paths))
        returned = self._collect(sources)
        self._duplicate_funcs |= self._local_config.duplicate_funcs
        for (path, name, line) in sorted(self._duplicate_funcs):
            _logger.warning('Duplicate function definition, File: {}, Name: {}, Line: {}'.format(path, name, line))

        if prepend_interactive:
            returned.insert(0, generate_interactive_test())

        hooks.tests_loaded(tests=returned) # pylint: disable=no-member
        returned.sort(key=lambda test: (
            test.__slash__.repeat_all_index, test.__slash__.get_sort_key()
        ))
        return returned


    def _generate_repeats(self, tests):
        returned = []
        repeat_each = config.root.run.repeat_each
        for test in tests:
            for i in range(repeat_each * repeat_marker.get_value(test.get_test_function(), 1)):
                returned.append(test.clone() if i else test)
        num_tests = len(returned)
        for i in range(config.root.run.repeat_all - 1):
            for test in itertools.islice(returned, 0, num_tests):
                clone = test.clone()
                clone.__slash__.repeat_all_index = i + 1
                returned.append(clone)
        return returned


    def _collect(self, iterator):
        returned = []
        context.reporter.report_collection_start()
        try:
            for x in iterator:
                assert x.__slash__.id is None
                x.__slash__.allocate_id()
                returned.append(x)
                context.reporter.report_test_collected(returned, x)
        finally:
            context.reporter.report_collection_end(returned)
        context.session.increment_total_num_tests(len(returned))
        return returned

    def _generate_test_sources(self, thing, matcher=None):

        if isinstance(thing, tuple):
            assert len(thing) == 2, '_generate_test_sources on tuples requires a tuple of (loadable_obj, matcher)'
            iterator = self._generate_test_sources(thing[0], matcher=thing[1])

        elif isinstance(thing, (list, GeneratorType, itertools.chain)):
            iterator = itertools.chain.from_iterable(self._generate_test_sources(x) for x in thing)
        elif isinstance(thing, string_types):
            iterator = self._iter_test_address(thing)
        elif isinstance(thing, RunnableTest):
            iterator = [thing]
        elif isinstance(thing, ResumedTestData):
            iterator = self._iter_test_resume(thing)
        elif not isinstance(thing, RunnableTestFactory):
            thing = self._get_runnable_test_factory(thing)
            iterator = thing.generate_tests(fixture_store=context.session.fixture_store)

        return (t for t in iterator if matcher is None or matcher.matches(t.__slash__))

    def _iter_test_resume(self, resume_state):
        for test in self._iter_path(resume_state.file_name):
            if resume_state.function_name == test.__slash__.address_in_file:
                if resume_state.variation:
                    if not resume_state.variation == test.get_variation().id:
                        continue
                yield test

    def _iter_test_address(self, address):
        drive, address = os.path.splitdrive(address)
        if ':' in address:
            path, address_in_file = address.split(':', 1)
        else:
            path = address
            address_in_file = None
        path = os.path.join(drive, path)


        tests = list(self._iter_path(path))

        # special case for directories where we couldn't load any tests (without filter)
        if not tests and address_in_file is None:
            return

        matched = False
        for test in tests:

            if address_in_file is not None:
                if not self._address_in_file_matches(address_in_file, test):
                    continue
            matched = True
            yield test
        if not matched:
            raise CannotLoadTests('Cannot find test(s) for {!r}'.format(address))

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
                msg = "Path {!r} could not be found".format(path)
                with handling_exceptions():
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
                        if not config.root.run.message_assertion_introspection:
                            dessert.disable_message_introspection()
                        with dessert.rewrite_assertions_context():
                            module = import_file(file_path)
                except Exception as e:

                    tb_file, tb_lineno, _, _ = _extract_tb()
                    raise mark_exception_handled(
                        CannotLoadTests(
                            "Could not load {0!r} ({1}:{2} - {3})".format(file_path, tb_file, tb_lineno, e)))
                if module is not None:
                    self._duplicate_funcs |= check_duplicate_functions(file_path)
                    with self._adding_local_fixtures(file_path, module):
                        for runnable in self._iter_runnable_tests_in_module(file_path, module):
                            if self._is_excluded(runnable):
                                continue
                            yield runnable

    @contextmanager
    def _adding_local_fixtures(self, file_path, module):
        with context.session.fixture_store.new_namespace_context():
            self._local_config.push_path(os.path.dirname(file_path))
            try:
                context.session.fixture_store.add_fixtures_from_dict(
                    self._local_config.get_dict())
                with context.session.fixture_store.new_namespace_context():
                    context.session.fixture_store.add_fixtures_from_dict(
                        vars(module))
                    context.session.fixture_store.resolve()
                    yield
            finally:
                self._local_config.pop_path()


    def _is_excluded(self, test):
        matchers = self._get_matchers()
        if matchers is None:
            return False
        return not all(m.matches(test.__slash__) for m in matchers)

    def _is_file_wanted(self, filename):
        return filename.endswith(".py")

    def _iter_runnable_tests_in_module(self, file_path, module):
        for thing_name in sorted(dir(module)):
            thing = getattr(module, thing_name)
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
            if is_valid_test_name(thing.__name__):
                return FunctionTestFactory(thing)

        return None


def _walk(p):
    if os.path.isfile(p):
        yield p
        return

    for path, dirnames, filenames in os.walk(p):
        dirnames[:] = sorted(dirname for dirname in dirnames if not dirname.startswith('.'))
        for filename in sorted(filenames):
            yield os.path.join(path, filename)

def _extract_tb():
    _, exc_value, exc_tb = sys.exc_info()
    returned = traceback.extract_tb(exc_tb)
    return returned[-1 - get_exception_frame_correction(exc_value)]
