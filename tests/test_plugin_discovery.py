import os

from slash import plugins

import pytest



def test_plugin_discovery(no_plugins, root_path, expected_names, config_override):
    config_override("plugins.search_paths", [root_path])
    plugins.manager.discover()
    assert set(plugins.manager.get_installed_plugins().keys()) == expected_names


@pytest.fixture
def root_path(tmpdir):
    return str(tmpdir.join('root_path'))

@pytest.fixture
def expected_names(root_path):
    returned = set()
    for index, path in enumerate([
            "a/b/p1.py",
            "a/b/p2.py",
            "a/p3.py",
            "a/b/c/p4.py",
    ]):
        plugin_name = "auto_plugin_{0}".format(index)
        path = os.path.join(root_path, path)
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as f:
            f.write("""
import slash.plugins
from slash.plugins.interface import PluginInterface

class {name}(PluginInterface):
    def get_name(self):
        return {name!r}

def install_plugins():
""".format(name=plugin_name))
            if index % 2 == 0:
                # don't install
                f.write("     pass")
            else:
                returned.add(plugin_name)
                f.write("     slash.plugins.manager.install({name}())".format(name=plugin_name))
    for junk_file in [
            "a/junk1.p",
            "a/b/junk2",
            "a/b/c/junk3",
    ]:
        with open(os.path.join(root_path, junk_file), "w") as f:
            f.write("---JUNK----")
    return returned
