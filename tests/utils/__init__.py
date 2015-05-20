from types import FunctionType
import itertools
import platform
import shutil
import sys
import tempfile

import forge
import logbook
from logbook.compat import LoggingHandler

import gossip
import slash
from slash.conf import config
from slash._compat import ExitStack
from slash.core.runnable_test import RunnableTest
from slash.core.test import TestTestFactory
from slash.core.function_test import FunctionTestFactory

if platform.python_version() < "2.7":
    import unittest2 as unittest
else:
    import unittest


_logger = logbook.Logger(__name__)


class TestCase(unittest.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self._handler = LoggingHandler()
        self._handler.push_application()
        self.addCleanup(self._handler.pop_application)
        gossip.get_group('slash').set_exception_policy(gossip.RaiseImmediately())
        self.override_config("log.console_level", 10000)  # silence console in tests

    def override_config(self, path, value):
        self.addCleanup(config.assign_path, path, config.get_path(path))
        config.assign_path(path, value)

    def get_new_path(self):
        returned = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, returned)
        return returned

    _forge = None

    @property
    def forge(self):
        if self._forge is None:
            self._forge = forge.Forge()
        return self._forge
    _events = None

    @property
    def events(self):
        if self._events is None:
            self._events = self.forge.create_wildcard_mock()
        return self._events

    def tearDown(self):
        if self._forge is not None:
            self._forge.restore_all_replacements()
            self._forge.verify()
        super(TestCase, self).tearDown()


class NullFile(object):

    def write(self, s):
        pass

    def isatty(self):
        return False

    def flush(self):
        pass


class CustomException(Exception):

    @classmethod
    def do_raise(cls):
        raise cls("Custom exception")


def no_op(*args, **kwargs):
    pass


def run_tests_in_session(test_class_path_or_iterator, session=None):
    with ExitStack() as stack:
        if session is None:
            session = slash.Session()
            stack.enter_context(session)

        test_class_path_or_iterator = make_runnable_tests(test_class_path_or_iterator)

        with session.get_started_context():
            slash.runner.run_tests(test_class_path_or_iterator)
    for result in session.results.iter_test_results():
        for err in itertools.chain(result.get_errors(), result.get_failures(), result.get_skips()):
            _logger.debug("Unsuccessful result: {0}", err)
    return session
run_tests_in_session.__test__ = False


def run_tests_assert_success(test_class_path_or_iterator, session=None):
    session = run_tests_in_session(test_class_path_or_iterator, session=session)
    assert session.results.is_success(), "Run did not succeed"
    return session

run_tests_assert_success.__test__ = False


def make_runnable_tests(thing):
    return slash.loader.Loader().get_runnables(thing)


def without_pyc(filename):
    if filename.endswith('.pyc'):
        return filename[:-1]
    return filename
