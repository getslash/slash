from types import FunctionType
from contextlib import contextmanager
import itertools
import platform
import shutil
import sys
import tempfile

import forge
import logbook
from logbook.compat import LoggingHandler
import pytest

import gossip
import slash
from slash._compat import PY2, PYPY
from slash.conf import config
from slash._compat import ExitStack
from slash.core.runnable_test import RunnableTest
from slash.core.test import TestTestFactory
from slash.core.function_test import FunctionTestFactory
from slash.plugins import PluginInterface

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


class NamedPlugin(PluginInterface):

    def get_name(self):
        return type(self).__name__


def no_op(*args, **kwargs):  # pylint: disable=unused-argument
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


def resolve_and_run(thing):
    slash.context.session.fixture_store.resolve()
    with slash.context.session.get_started_context():
        tests = make_runnable_tests(thing)
        slash.runner.run_tests(tests)

    return list(slash.context.session.results.iter_test_results())


def without_pyc(filename):
    if filename.endswith('.pyc'):
        return filename[:-1]
    return filename


def raises_maybe(exc, cond):
    @contextmanager
    def noop():
        yield

    if cond:
        return pytest.raises(exc)
    return noop()

_noop = lambda f: f

if PY2:
    skip_on_py2 = pytest.mark.skip
else:
    skip_on_py2 = _noop

if PYPY:
    skip_on_pypy = pytest.mark.skip
else:
    skip_on_pypy = _noop


class Unprintable(object):

    def __repr__(self):
        1/0                     # pylint: disable=pointless-statement

    __str__ = __repr__


def maybe_decorate(decorator, flag):

    def returned(func):
        if flag:
            func = decorator(func)
        return func
    return returned
