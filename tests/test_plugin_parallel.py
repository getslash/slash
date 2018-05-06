# pylint: disable=superfluous-parens,protected-access
from slash.utils.marks import mark, try_get_mark
from slash import Session
from slash.utils import parallel_utils
import pytest
import slash.plugins


@pytest.mark.parametrize('session_state', ['not_parallel', 'parent', 'child'])
@pytest.mark.parametrize('plugin_parallel_mode', parallel_utils.ParallelPluginModes.MODES)
def test_parallel_mode(plugin, config_override, session_state, plugin_parallel_mode):
    slash.plugins.manager._pending_deactivation = set()

    if not session_state == 'not_parallel':
        config_override("parallel.num_workers", 1)
    if session_state == 'child':
        config_override("parallel.worker_id", 1)

    if session_state == 'not_parallel':
        assert not parallel_utils.is_parallel_session()
        assert not parallel_utils.is_parent_session()
        assert not parallel_utils.is_child_session()
    if session_state == 'parent':
        assert parallel_utils.is_parallel_session()
        assert parallel_utils.is_parent_session()
        assert not parallel_utils.is_child_session()
    if session_state == 'child':
        assert parallel_utils.is_parallel_session()
        assert parallel_utils.is_child_session()
        assert not parallel_utils.is_parent_session()

    plugin = mark('parallel_mode', plugin_parallel_mode)(plugin)
    assert try_get_mark(plugin, 'parallel_mode') == plugin_parallel_mode

    slash.plugins.manager.install(plugin)
    slash.plugins.manager.configure_for_parallel_mode()
    is_plugin_in_deactivation_list = plugin.get_name() in slash.plugins.manager._pending_deactivation
    if plugin_parallel_mode == parallel_utils.ParallelPluginModes.ENABLED:
        assert not is_plugin_in_deactivation_list
    elif plugin_parallel_mode == parallel_utils.ParallelPluginModes.DISABLED:
        assert is_plugin_in_deactivation_list if session_state != "not_parallel" else not is_plugin_in_deactivation_list
    elif plugin_parallel_mode == parallel_utils.ParallelPluginModes.PARENT_ONLY:
        assert is_plugin_in_deactivation_list if session_state == "child" else not is_plugin_in_deactivation_list
    elif plugin_parallel_mode == parallel_utils.ParallelPluginModes.CHILD_ONLY:
        assert is_plugin_in_deactivation_list if session_state == "parent" else not is_plugin_in_deactivation_list


@pytest.mark.parametrize('is_parallel_mode', [True, False])
def test_parallel_mode_activation_causes_warning(config_override, checkpoint, is_parallel_mode):

    @slash.plugins.parallel_mode(parallel_utils.ParallelPluginModes.DISABLED)
    class Plugin(slash.plugins.PluginInterface):
        def session_start(self):
            checkpoint()

        def get_name(self):
            return type(self).__name__.lower()

    if is_parallel_mode:
        config_override("parallel.num_workers", 1)
        assert parallel_utils.is_parallel_session()
    plugin = Plugin()
    assert try_get_mark(plugin, 'parallel_mode') == parallel_utils.ParallelPluginModes.DISABLED
    with Session():
        slash.plugins.manager.install(plugin)
        slash.plugins.manager.activate(plugin)
        slash.hooks.session_start() # pylint: disable=no-member

        warning_message_expected = "Activating plugin {} though it's configuration for parallel mode doesn't fit to current session"\
                                    .format(plugin.get_name())
        is_warning_appeared = warning_message_expected in [warning.message for warning in slash.session.warnings]
        assert is_warning_appeared if is_parallel_mode else not is_warning_appeared
        assert checkpoint.called
