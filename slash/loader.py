from .exceptions import CannotLoadTests
from .exception_handling import handling_exceptions
from .runnable_test_factory import RunnableTestFactory
from .ctx import context
from contextlib import contextmanager
from logbook import Logger # pylint: disable=F0401
from emport import import_file
from ._compat import iteritems # pylint: disable=F0401
import os
import sys

_logger = Logger(__name__)

class Loader(object):
    """
    Provides iteration interfaces to load runnable tests from various places
    It also enables execution of single class/method within a module, using the syntax test_object.py:TestClass.test_method 
    """
    def iter_path(self, path):
        return self.iter_paths([path])
    def iter_paths(self, paths):
        paths = list(paths)
        for path in paths:
            if ":" in path:
                _logger.debug("Path {0} contains ':'. verify module exists".format(path))
                path = path.split(":", 1)[0]
            if not os.path.exists(path):
                raise CannotLoadTests("Path {0} could not be found".format(path))
        for path in paths:
            if ":" in path:
                path, name = path.split(":", 1)
            else:
                path, name = path, None

            for file_path in _walk(path):
                _logger.debug("Checking {0}", file_path)
                if not self._is_file_wanted(file_path):
                    _logger.debug("{0} is not wanted. Skipping...", file_path)
                    continue
                with self._handling_import_errors():
                    module = import_file(file_path)
                for runnable in self._iter_runnable_tests_in_module(module, name):
                    yield runnable

    @contextmanager
    def _handling_import_errors(self):
        try:
            with handling_exceptions(context="during import"):
                yield
        except Exception: # pylint: disable=W0703
            if not context.session:
                raise
            context.session.result.global_result.add_error()

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

    def _iter_runnable_tests_in_module(self, module, name):
        if name:
            if "." in name:
                test_class_name, test_method_name = name.split(".", 1)
                _logger.debug("Found a period.")
            else:
                test_class_name, test_method_name = name, None
                _logger.debug("No period found, working on the whole class")
        else:
            test_class_name, test_method_name = None, None
            _logger.debug("No : found, working on the whole module")
        _logger.debug("test_class_name={}, test_method_name={}".format(test_class_name, test_method_name))

        for factory_name, factory in iteritems(vars(module)):
            if factory is RunnableTestFactory: # probably imported directly
                continue
            if test_class_name and factory_name != test_class_name:
                continue
            if isinstance(factory, type) and issubclass(factory, RunnableTestFactory):
                _logger.debug("Getting tests from {0}:{1}..", module, factory_name)
                for test in self.iter_test_factory(factory):
                    if test_method_name and test_method_name != test.get_test_method():
                        continue
                    yield test

def _walk(p):
    if os.path.isfile(p):
        return [p]
    return (os.path.join(dirname, filename)
            for dirname, _, filenames in os.walk(p)
            for filename in filenames)
