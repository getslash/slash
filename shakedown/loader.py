from six import iteritems # pylint: disable=F0401
from .utils.imports import import_file
from .runnable_test_factory import RunnableTestFactory
from logbook import Logger # pylint: disable=F0401
import os
import sys

_logger = Logger(__name__)

class Loader(object):
    """
    Provides iteration interfaces to load runnable tests from various places
    """
    def iter_path(self, path):
        for file_path in _walk(path):
            _logger.debug("Checking {0}", file_path)
            if not self._is_file_wanted(file_path):
                _logger.debug("{0} is not wanted. Skipping...", file_path)
                continue
            module = import_file(file_path)
            for runnable in self._iter_runnable_tests_in_module(module):
                yield runnable

    def iter_test_factory(self, factory):
        for test in factory.generate_tests():
            yield test

    def iter_package(self, package_name):
        if package_name not in sys.modules:
            __import__(package_name)
        path = sys.modules[package_name].__file__
        if os.path.basename(path) in ("__init__.py", "__init__.pyc"):
            path = os.path.dirname(path)
        return self.iter_path(path)

    def _is_file_wanted(self, filename):
        return filename.endswith(".py")

    def _iter_runnable_tests_in_module(self, module):
        for factory_name, factory in iteritems(vars(module)):
            if factory is RunnableTestFactory: # probably imported directly
                continue
            if isinstance(factory, type) and issubclass(factory, RunnableTestFactory):
                _logger.debug("Getting tests from {0}:{1}..", module, factory_name)
                for test in self.iter_test_factory(factory):
                    yield test

def _walk(p):
    if os.path.isfile(p):
        return [p]
    return (os.path.join(dirname, filename)
            for dirname, _, filenames in os.walk(p)
            for filename in filenames)
