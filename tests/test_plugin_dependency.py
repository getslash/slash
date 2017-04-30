import pytest
import slash.plugins
from .conftest import Checkpoint
from slash.plugins import PluginInterface
from gossip.exceptions import CannotResolveDependencies


@pytest.mark.parametrize('needs_decorate_method', [True, False])
@pytest.mark.parametrize('provides_decorate_method', [True, False])
def test_needs_provides_plugin_name(needs_decorate_method, provides_decorate_method, checkpoint1, checkpoint2):

    @slash.plugins.active  # pylint: disable=abstract-method, unused-variable
    @_maybe_decorate(slash.plugins.needs('p'), not needs_decorate_method)
    @autoname
    class NeedsPlugin(PluginInterface):

        @_maybe_decorate(slash.plugins.needs('p'), needs_decorate_method)
        def session_start(self):
            checkpoint2()

    @slash.plugins.active  # pylint: disable=abstract-method, unused-variable
    @_maybe_decorate(slash.plugins.provides('p'), not provides_decorate_method)
    @autoname
    class ProvidesPlugin(PluginInterface):

        @_maybe_decorate(slash.plugins.provides('p'), provides_decorate_method)
        def session_start(self):
            checkpoint1()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint1.timestamp < checkpoint2.timestamp


def test_provides_globally_needs_globally(checkpoint1, checkpoint2):
    '''
    Plugin A: Provides x at class level
    Plugin B: Needs x at class level
    '''
    @slash.plugins.provides('x')
    class PluginA(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_a'

        def session_start(self):
            checkpoint1()

        def test_start(self):
            pass


    @slash.plugins.needs('x')
    class PluginB(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_b'

        def session_start(self):
            checkpoint2()

        def error_added(self, result, error): # pylint: disable=unused-argument
            pass

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint1.timestamp < checkpoint2.timestamp

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])


def test_provides_globally_needs_specific_hook(checkpoint1, checkpoint2):
    '''
    Plugin A: Provides x at class level
    Plugin B: Needs x for specific hook
    '''
    @slash.plugins.provides('x')
    class PluginA(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_a'

        def session_start(self):
            checkpoint1()

        def test_start(self):
            pass


    class PluginB(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_b'

        @slash.plugins.needs('x')
        def session_start(self):
            checkpoint2()

        def error_added(self, result, error): # pylint: disable=unused-argument
            pass

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint1.timestamp < checkpoint2.timestamp

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])


def test_provides_globally_needs_specific_hook_which_does_not_exist_at_a(checkpoint2):
    '''
    Plugin A: Provides x at class level
    Plugin B: Needs x for specific hook, this hook does not definied in A

    Expectations:
    Should work in the empty sense
    all non-needing hooks should work, even when missing from A, the specific hook needs to happen in A before B.
    '''
    @slash.plugins.provides('x')
    class PluginA(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_a'

        def test_start(self):
            pass


    class PluginB(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_b'

        @slash.plugins.needs('x')
        def session_start(self):
            checkpoint2()

        def error_added(self, result, error): # pylint: disable=unused-argument
            pass

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint2.called

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])


def test_provides_specific_hook_needs_globally(checkpoint1, checkpoint2):
    '''
    Plugin A: Provides x on a specific hook
    Plugin B: Needs x at class level

    Expectations:
    This case should fail, because logically the other hooks don't have anyone to provide X for them
    '''
    class PluginA(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_a'

        @slash.plugins.provides('x')
        def session_start(self):
            checkpoint1()

        def test_start(self):
            pass


    @slash.plugins.needs('x')
    class PluginB(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_b'

        def session_start(self):
            checkpoint2()

        def error_added(self, result, error): # pylint: disable=unused-argument
            pass

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])


def test_provides_specific_hook_needs_globally_with_this_hook_only(checkpoint1, checkpoint2):
    '''
    Plugin A: Provides x on a specific hook
    Plugin B: Needs x at class level, but only has one hook (the one provided by A)
    '''
    class PluginA(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_a'

        @slash.plugins.provides('x')
        def session_start(self):
            checkpoint1()

        def test_start(self):
            pass


    @slash.plugins.needs('x')
    class PluginB(slash.plugins.interface.PluginInterface):

        def get_name(self):
            return 'plugin_b'

        def session_start(self):
            checkpoint2()

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint1.timestamp < checkpoint2.timestamp

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])


@pytest.mark.parametrize('needs_parent_level', [True, False])
@pytest.mark.parametrize('provides_parent_level', [True, False])
def test_provides_needs_with_inheritence_on_class_level(checkpoint, checkpoint1, checkpoint2, needs_parent_level, provides_parent_level):
    '''
    Plugin A: Provides x in class level (by it self or by inheritence)
    Plugin b: Needs x in class level (by it self or by inheritence)
    '''
    # pylint: disable=abstract-method

    @_maybe_decorate(slash.plugins.provides('x'), provides_parent_level)
    class PluginAParent(slash.plugins.interface.PluginInterface):

        def test_start(self):
            pass

    @_maybe_decorate(slash.plugins.provides('x'), not provides_parent_level)
    class PluginA(PluginAParent):

        def get_name(self):
            return 'plugin_a'

        def session_start(self):
            checkpoint1()


    @_maybe_decorate(slash.plugins.needs('x'), needs_parent_level)
    class PluginBParent(slash.plugins.interface.PluginInterface):

        def error_added(self, result, error): # pylint: disable=unused-argument
            checkpoint()


    @_maybe_decorate(slash.plugins.needs('x'), not needs_parent_level)
    class PluginB(PluginBParent):

        def get_name(self):
            return 'plugin_b'

        def session_start(self):
            checkpoint2()

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    # session_start hook should be provided the PluginA.session_start method
    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint1.timestamp < checkpoint2.timestamp

    # error_added hook should be provided by empty registration of pluginA
    slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member
    assert checkpoint.called

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.error_added()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])

    # Ensure only hooks required by PluginB fails
    slash.hooks.test_end()  # pylint: disable=no-member


def test_provides_needs_in_both_inheritence_levels(checkpoint, checkpoint1, checkpoint2):
    # pylint: disable=abstract-method

    @slash.plugins.provides('x')
    class PluginAParent(slash.plugins.interface.PluginInterface):

        def test_start(self):
            pass

    @slash.plugins.provides('y')
    class PluginA(PluginAParent):

        def get_name(self):
            return 'plugin_a'

        def session_start(self):
            checkpoint1()


    @slash.plugins.needs('x')
    class PluginBParent(slash.plugins.interface.PluginInterface):

        def error_added(self, result, error): # pylint: disable=unused-argument
            checkpoint()


    @slash.plugins.needs('y')
    class PluginB(PluginBParent):

        def get_name(self):
            return 'plugin_b'

        def session_start(self):
            checkpoint2()

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    # session_start hook should be provided the PluginA.session_start method
    slash.hooks.session_start()  # pylint: disable=no-member
    assert checkpoint1.timestamp < checkpoint2.timestamp

    # error_added hook should be provided by empty registration of pluginA
    slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member
    assert checkpoint.called

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y'])

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.error_added()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y'])

    # Ensure only hooks required by PluginB fails
    slash.hooks.test_end()  # pylint: disable=no-member


def test_provides_needs_with_inheritence_on_method_level(checkpoint):
    '''
    Plugin A: Provides x in method level (by it self or by inheritence) to test_start & session_start
    Plugin b: Needs x in method level (by it self or by inheritence) on test_start & session_start
    '''
    # pylint: disable=abstract-method
    session_start_a = Checkpoint()
    session_start_b = Checkpoint()
    test_start_a = Checkpoint()
    test_start_b = Checkpoint()

    class PluginAParent(slash.plugins.interface.PluginInterface):

        @slash.plugins.provides('x')
        def test_start(self):
            test_start_a()

    class PluginA(PluginAParent):

        def get_name(self):
            return 'plugin_a'

        @slash.plugins.provides('x')
        def session_start(self):
            session_start_a()


    class PluginBParent(slash.plugins.interface.PluginInterface):

        @slash.plugins.needs('x')
        def session_start(self):
            session_start_b()

        def error_added(self, result, error): # pylint: disable=unused-argument
            checkpoint()


    class PluginB(PluginBParent):

        def get_name(self):
            return 'plugin_b'

        @slash.plugins.needs('x')
        def test_start(self):
            test_start_b()

    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert session_start_a.timestamp < session_start_b.timestamp

    slash.hooks.test_start()  # pylint: disable=no-member
    assert test_start_a.timestamp < test_start_b.timestamp

    # error_added hook should not need anything
    slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member
    assert checkpoint.called

    slash.plugins.manager.deactivate('plugin_a')
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])
    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.test_start()  # pylint: disable=no-member
    slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x'])


def test_provides_needs_with_child_overrides():
    # pylint: disable=line-too-long
    '''
    | Hook Name     | Plugin A                                                                | Plugin B                                                               |
    |---------------+-------------------------------------------------------------------------+------------------------------------------------------------------------|
    | session_start | Child Provides x in method level, overrides parent's empty registration | Needs x (Parent) & y (Child) in class level                            |
    | test_start    | Child Provides x in method level, overrides parent's real registration  | Needs x (Parent) & y (Child) in class level                            |
    | error_added   | x is not provided, overrides parent's real registration                 | Needs x (Parent) & y (Child) in class level                            |
    | test_end      | x is not provided, overrides parent's empty registration                | Needs x (Parent) & y (Child) in class level                            |
    | session_end   | Parent provides x, child provides y - both in class level               | Needs x (Parent) & y (Child) in class level, z in (child) method level |
    '''
    # pylint: disable=abstract-method
    session_start_a = Checkpoint()
    session_start_b = Checkpoint()
    test_start_a = Checkpoint()
    test_start_b = Checkpoint()

    @slash.plugins.provides('x')
    class PluginAParent(slash.plugins.interface.PluginInterface):

        def test_start(self):
            test_start_a()

        def error_added(self, result, error): # pylint: disable=unused-argument
            pass

        def session_end(self):
            pass

    @slash.plugins.provides('y')
    class PluginA(PluginAParent):

        def get_name(self):
            return 'plugin_a'

        @slash.plugins.provides('x')
        def session_start(self):
            # Overrides empty registration of PluginAParent
            session_start_a()

        @slash.plugins.provides('x')
        def test_start(self):
            # Overrides "real" registration of PluginAParent
            test_start_a()

        def error_added(self, result, error): # pylint: disable=unused-argument
            # Overrides "real" registration of PluginAParent
            pass

        def test_end(self):
            # Overrides empty registration of PluginAParent
            pass


    @slash.plugins.needs('x')
    class PluginBParent(slash.plugins.interface.PluginInterface):

        def session_start(self):
            session_start_b()

        def error_added(self, result, error): # pylint: disable=unused-argument
            pass

        def test_start(self):
            test_start_b()

        def test_end(self):
            pass


    @slash.plugins.needs('y')
    class PluginB(PluginBParent):

        def get_name(self):
            return 'plugin_b'

        @slash.plugins.needs('z')
        def session_end(self):
            pass


    for plugin_cls in [PluginA, PluginB]:
        slash.plugins.manager.install(plugin_cls(), activate_later=True)
    slash.plugins.manager.activate_pending_plugins()

    slash.hooks.session_start()  # pylint: disable=no-member
    assert session_start_a.timestamp < session_start_b.timestamp

    slash.hooks.test_start()  # pylint: disable=no-member
    assert test_start_a.timestamp < test_start_b.timestamp

    slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member

    slash.hooks.test_end()  # pylint: disable=no-member

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_end()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['z'])


    slash.plugins.manager.deactivate('plugin_a')

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y'])

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.test_start()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y'])

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.error_added(result=None, error=None)  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y'])

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.test_end()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y'])

    with pytest.raises(CannotResolveDependencies) as caught:
        slash.hooks.session_end()  # pylint: disable=no-member
    assert caught.value.unmet_dependencies == set(['x', 'y', 'z'])

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
