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
        for object_name, obj in iteritems(vars(module)):
            if obj is RunnableTestFactory:
                continue
            if isinstance(obj, type) and issubclass(obj, RunnableTestFactory):
                _logger.debug("Getting tests from {0}:{1}..", module, object_name)
                for test in obj().generate_tests():
                    yield test

def _walk(p):
    if os.path.isfile(p):
        return [p]
    return (os.path.join(dirname, filename)
            for dirname, _, filenames in os.walk(p)
            for filename in filenames)
