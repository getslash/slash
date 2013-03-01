import imp
import itertools
import os
import sys
import platform

_IS_PYTHON_3_3 = (platform.python_version() >= "3.3")

from logbook import Logger # pylint: disable=F0401

_logger = Logger(__name__)

class NoInitFileFound(Exception):
    pass

def import_file(filename):
    module_name = _setup_module_name_for_import(filename)
    returned = __import__(module_name, fromlist=[''])
    return returned

_package_name_generator = ('_{0}'.format(x) for x in itertools.count())

def _generate_package_name():
    for suggested in _package_name_generator:
        if not _package_name_exists(suggested):
            return suggested

def _package_name_exists(pkg_name):
    return pkg_name in sys.modules

def _setup_module_name_for_import(filename):
    return _create_new_module_name(filename)

_cached_package_names = {}

def _create_new_module_name(filename):
    _logger.debug("Creating new package for {0}", filename)
    nonpackage_dir, remainder = _split_nonpackage_dir(filename)
    _logger.debug("After split: {0}, {1}", nonpackage_dir, remainder)
    package_name = _cached_package_names.get(nonpackage_dir, None)
    if package_name is None:
        package_name = _generate_package_name()
        sys.modules[package_name] = _create_package_module(package_name, nonpackage_dir)
        _cached_package_names[nonpackage_dir] = package_name
    return '{0}.{1}'.format(package_name, remainder)

def _split_nonpackage_dir(path):
    if not os.path.isdir(path):
        nonpackage_dir, module = os.path.split(os.path.normpath(os.path.abspath(path)))
        module = _make_module_name(module).split(".")
    else:
        nonpackage_dir = path
        module = []
    while os.path.isfile(os.path.join(nonpackage_dir, "__init__.py")):
        if '.' in os.path.split(nonpackage_dir)[-1]:
            # we cannot import from such packages, stop traversing upwards...
            break
        nonpackage_dir, current_component = os.path.split(nonpackage_dir)
        module.insert(0, current_component)
        _logger.debug("Now at {0}, {1}", nonpackage_dir, module)
    if not module:
        raise NoInitFileFound("Could not find __init__.py file in {0}".format(path))
    return nonpackage_dir, ".".join(module)

def _make_module_name(filename):
    assert filename.endswith('.py') or filename.endswith('.pyc')
    return filename.rsplit(".", 1)[0].replace(os.path.sep, ".")

def _create_package_module(name, path):
    imp.acquire_lock()
    try:
        if _IS_PYTHON_3_3:
            # the package import machinery works a bit differently in
            # python 3.3
            returned = imp.new_module(name)
            returned.__path__ = [path]
            sys.modules[name] = returned
        else:
            returned = imp.load_module(name, None, path, ('', '', imp.PKG_DIRECTORY))
    finally:
        imp.release_lock()
    return returned
