import os
import sys

import requests

from .conf import config

def load(thing=None):
    """
    Loads site files (customization files) from various locations.

    Without an argument, loads all default site customization options.

    With a specific argument, load that argument as a customization file (real file or URL).
    """
    if thing is None:
        return _load_defaults()
    _load_filename_or_url(thing)

def _load_defaults():
    _load_slashrc()
    _load_local_slashrc()
    _load_environment()
    _load_entry_points()

def _load_slashrc():
    _load_file_if_exists(os.path.expanduser(config.root.run.user_customization_file_path))

def _load_local_slashrc():
    _load_file_if_exists(os.path.abspath(os.path.expanduser(config.root.run.project_customization_file_path)))

def _load_file_if_exists(path):
    if os.path.isfile(path):
        old_sys_path = sys.path[:]
        sys.path.insert(0, os.path.dirname(path))
        try:
            _load_filename(path)
        finally:
            sys.path[:] = old_sys_path

def _load_environment():
    loaded_url_or_file = os.environ.get("SLASH_SETTINGS")
    if loaded_url_or_file:
        load(loaded_url_or_file)

def _load_entry_points():
    import pkg_resources
    for customize_function_loader in pkg_resources.iter_entry_points("slash.site.customize"): # pylint: disable=no-member
        func = customize_function_loader.load()
        func()

def _load_filename_or_url(filename_or_url):
    if os.path.isfile(filename_or_url):
        _load_filename(filename_or_url)
    else:
        _load_url(filename_or_url)

def _load_filename(filename):
    with open(filename, "r") as f:
        _load_source(f.read(), filename)

def _load_url(url):
    response = requests.get(url)
    response.raise_for_status()
    _load_source(response.content, url)

def _load_source(source, filename):
    code = compile(source, os.path.abspath(filename), 'exec')
    exec(code, {"__file__" : filename}) # pylint: disable=W0122
