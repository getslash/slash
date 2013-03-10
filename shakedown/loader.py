from six import iteritems # pylint: disable=F0401
from .utils.imports import import_file
from .runnable_test_factory import RunnableTestFactory
from logbook import Logger # pylint: disable=F0401
import os

_logger = Logger(__name__)

class Loader(object):
    """
    A class responsible for finding runnable tests in a path
    """
    def iter_runnable_tests(self, path):
        for file_path in _walk(path):
            _logger.debug("Checking {0}", file_path)
            if not self._is_file_wanted(file_path):
                _logger.debug("{0} is not wanted. Skipping...", file_path)
                continue
            module = import_file(file_path)
            for runnable in self._iter_runnable_tests_in_module(module):
                yield runnable

    def _is_file_wanted(self, filename):
        return filename.endswith(".py")

    def _iter_runnable_tests_in_module(self, module):
        for factory_name, factory in iteritems(vars(module)):
            if factory is RunnableTestFactory: # probably imported directly
                continue
            if isinstance(factory, type) and issubclass(factory, RunnableTestFactory):
                _logger.debug("Getting tests from {0}:{1}..", module, factory_name)
                for test in factory.generate_tests():
                    yield test

def _walk(p):
    if os.path.isfile(p):
        return [p]
    return (os.path.join(dirname, filename)
            for dirname, _, filenames in os.walk(p)
            for filename in filenames)
