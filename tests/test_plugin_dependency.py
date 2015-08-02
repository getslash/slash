import itertools

import pytest
import slash.plugins
from slash.plugins import PluginInterface


@pytest.mark.parametrize('needs_decorate_method', [True, False])
@pytest.mark.parametrize('provides_decorate_method', [True, False])
def test_needs_provides_plugin_name(needs_decorate_method, provides_decorate_method, checkpoint1, checkpoint2):

    @slash.plugins.active
    @_maybe_decorate(slash.plugins.needs('p'), not needs_decorate_method)
    @autoname
    class NeedsPlugin(PluginInterface):

        @_maybe_decorate(slash.plugins.needs('p'), needs_decorate_method)
        def session_start(self):
            checkpoint2()

    @slash.plugins.active
    @_maybe_decorate(slash.plugins.provides('p'), not provides_decorate_method)
    @autoname
    class ProvidesPlugin(PluginInterface):

        @_maybe_decorate(slash.plugins.provides('p'), provides_decorate_method)
        def session_start(self):
            checkpoint1()

    slash.hooks.session_start()
    assert checkpoint1.timestamp < checkpoint2.timestamp


def _maybe_decorate(decorator, flag):

    def returned(func):
        if flag:
            func = decorator(func)
        return func
    return returned


def autoname(plugin):
    def get_name(self):
        return type(self).__name__.lower()
    plugin.get_name = get_name
    return plugin
